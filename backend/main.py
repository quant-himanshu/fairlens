from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from api.audit import router as audit_router
from api.explain import router as explain_router
from api.datasets import router as datasets_router
from api.pipeline import router as pipeline_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FairLens API starting up...")
    yield
    logger.info("FairLens API shutting down.")


app = FastAPI(
    title="FairLens API",
    description="AI Bias Detection & Fairness Auditing Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://fairlens-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit_router, prefix="/api/audit", tags=["audit"])
app.include_router(explain_router, prefix="/api/explain", tags=["explain"])
app.include_router(pipeline_router, prefix="/api/pipeline", tags=["pipeline"])
app.include_router(datasets_router, prefix="/api/datasets", tags=["datasets"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "fairlens-api"}
