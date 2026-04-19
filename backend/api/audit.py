import uuid
import io
from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from models.schemas import AuditResult, AuditConfig, AuditStatus, MitigationRequest, MitigationResult
from core.bias_detector import BiasDetector
from core.mitigator import BiasMitigator
from utils.validators import validate_dataframe

router = APIRouter()

# In-memory audit store (swap for DB in production)
_audit_store: dict[str, tuple[AuditResult, pd.DataFrame, AuditConfig]] = {}


@router.post("/upload", response_model=AuditResult)
async def upload_and_audit(
    file: UploadFile = File(...),
    label_column: str = Form(...),
    ground_truth_column: str = Form(...),
    sensitive_attributes: str = Form(...),   # comma-separated
    score_column: str = Form(None),
):
    """
    Upload a CSV and immediately run the full bias audit.
    Returns a complete AuditResult including all 6 fairness metrics.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not parse CSV: {e}")

    attrs = [a.strip() for a in sensitive_attributes.split(",") if a.strip()]
    config = AuditConfig(
        label_column=label_column,
        ground_truth_column=ground_truth_column,
        sensitive_attributes=attrs,
        score_column=score_column or None,
    )

    errors = validate_dataframe(df, config)
    if errors:
        raise HTTPException(status_code=422, detail={"validation_errors": errors})

    detector = BiasDetector(df, config)
    output = detector.run()

    audit_id = str(uuid.uuid4())
    result = AuditResult(
        audit_id=audit_id,
        status=AuditStatus.COMPLETE,
        dataset_name=file.filename,
        row_count=len(df),
        sensitive_attributes=attrs,
        overall_verdict=output.overall_verdict,
        metrics=output.metrics,
        group_stats=output.group_stats,
        top_biased_feature=output.top_biased_feature,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    _audit_store[audit_id] = (result, df, config)
    return result


@router.get("/{audit_id}", response_model=AuditResult)
async def get_audit(audit_id: str):
    if audit_id not in _audit_store:
        raise HTTPException(status_code=404, detail="Audit not found.")
    return _audit_store[audit_id][0]


@router.post("/mitigate", response_model=MitigationResult)
async def mitigate(req: MitigationRequest):
    if req.audit_id not in _audit_store:
        raise HTTPException(status_code=404, detail="Audit not found.")

    _, df, config = _audit_store[req.audit_id]

    if req.sensitive_attribute not in config.sensitive_attributes:
        raise HTTPException(
            status_code=400,
            detail=f"'{req.sensitive_attribute}' was not audited. Choose from: {config.sensitive_attributes}",
        )

    mitigator = BiasMitigator(df, config, req.sensitive_attribute)
    result = mitigator.apply(req.strategy)
    return result


@router.get("/")
async def list_audits():
    return [
        {
            "audit_id": aid,
            "dataset_name": data[0].dataset_name,
            "overall_verdict": data[0].overall_verdict,
            "created_at": data[0].created_at,
        }
        for aid, data in _audit_store.items()
    ]
