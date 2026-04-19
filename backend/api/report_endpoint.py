"""
Extends audit.py with a PDF download endpoint.
Add this import + route to api/audit.py
"""

# Add to api/audit.py:

from fastapi.responses import StreamingResponse as _StreamingResponse
import io as _io
from core.report_gen import generate_pdf as _gen_pdf

# Route to add inside audit router:
# @router.get("/{audit_id}/report.pdf")
# async def download_report(audit_id: str):
#     if audit_id not in _audit_store:
#         raise HTTPException(status_code=404, detail="Audit not found.")
#     audit_result, _, _ = _audit_store[audit_id]
#     explanation = _explain_cache.get(audit_id)
#     pdf_bytes = _gen_pdf(audit_result, explanation)
#     return _StreamingResponse(
#         _io.BytesIO(pdf_bytes),
#         media_type="application/pdf",
#         headers={"Content-Disposition": f"attachment; filename=fairlens-audit-{audit_id[:8]}.pdf"},
#     )
