from fastapi import APIRouter
from utils.explainer import explain_bias_with_gemini

router = APIRouter()

@router.get("/")
async def explain_bias(metric: str, value: float):
    return {"explanation": explain_bias_with_gemini(metric, value)}
