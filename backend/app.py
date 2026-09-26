from pathlib import Path
from typing import Optional, Any
import math

from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.final_recommendation_pipeline_v2 import FinalRecommendationPipelineV2

BASE_DIR = Path(__file__).resolve().parent
ENGINE = FinalRecommendationPipelineV2(BASE_DIR)

app = FastAPI(
    title="Food Packaging AI Recommendation API",
    version="1.0.0",
    description=(
        "Evidence-guided AI-assisted food packaging material recommendation API. "
        "The API wraps the integrated deterministic, requirement-aware, ML-enhanced "
        "and optimization pipeline."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.middleware("http")
async def strip_api_prefix(request, call_next):
    """
    Allow the same FastAPI routes to work locally as /foods
    and through Vercel Services as /api/foods.
    """
    path = request.scope.get("path", "")

    if path == "/api":
        request.scope["path"] = "/"
        request.scope["raw_path"] = b"/"

    elif path.startswith("/api/"):
        new_path = path[4:]
        request.scope["path"] = new_path
        request.scope["raw_path"] = new_path.encode("utf-8")

    return await call_next(request)



class RecommendationRequest(BaseModel):
    food_name: str = Field(..., min_length=1, description="Food commodity name.")
    top_n: int = Field(3, ge=1, le=10, description="Number of recommendations.")
    storage_type: Optional[str] = Field(None, description="Storage condition/type.")
    shelf_life_days: Optional[float] = Field(None, ge=0, description="Target shelf life in days.")
    humidity: Optional[str] = Field(None, description="Humidity condition.")
    transport: Optional[str] = Field(None, description="Transport condition.")
    map_required: Optional[bool] = Field(None, description="Whether MAP is required.")


def _json_safe(value):
    if isinstance(value, float):
        return None if not math.isfinite(value) else value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "food-packaging-ai-recommendation-api",
        "version": app.version,
        "engine": "FinalRecommendationPipelineV2",
    }


@app.get("/metadata")
def metadata():
    return {
        "foods": int(ENGINE.requirements.df["Food_ID"].nunique()),
        "packaging_materials": int(ENGINE.base.packages["Packaging_ID"].nunique()),
        "candidate_pairs": int(len(ENGINE.base.df)),
        "eligible_candidate_pairs": int((ENGINE.base.df["Evidence_Corrected_Compatibility_Class"] != "Insufficient_Evidence").sum()),
        "top_n_max": 10,
    }


@app.get("/foods")
def foods():
    cols = [c for c in ["Food_ID", "Food_Name", "Food_Category", "Food_Subcategory"] if c in ENGINE.requirements.df.columns]
    df = ENGINE.requirements.df[cols].drop_duplicates().sort_values(["Food_Category", "Food_Name"], na_position="last")
    return {"count": len(df), "foods": jsonable_encoder(df.to_dict(orient="records"))}


@app.get("/packaging")
def packaging():
    preferred = [
        "Packaging_ID", "Packaging_Material", "Material_Category",
        "Structure_Type", "Sealability", "Gas_Permeability", "MAP_Suitability",
        "Mechanical_Strength"
    ]
    cols = [c for c in preferred if c in ENGINE.base.packages.columns]
    df = ENGINE.base.packages[cols].drop_duplicates("Packaging_ID").sort_values("Packaging_Material", na_position="last")
    return {"count": len(df), "packaging": jsonable_encoder(df.to_dict(orient="records"))}


@app.post("/recommend")
def recommend(request: RecommendationRequest):
    try:
        result = ENGINE.recommend(
            food_name=request.food_name,
            top_n=request.top_n,
            storage_type=request.storage_type,
            shelf_life_days=request.shelf_life_days,
            humidity=request.humidity,
            transport=request.transport,
            map_required=request.map_required,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Recommendation engine error: {exc}")

    return _json_safe(jsonable_encoder(result))


@app.post("/recommend/batch")
def recommend_batch(requests: list[RecommendationRequest]):
    if not requests:
        raise HTTPException(status_code=400, detail="At least one request is required.")
    if len(requests) > 50:
        raise HTTPException(status_code=400, detail="Batch size cannot exceed 50 requests.")

    results = []
    for req in requests:
        try:
            result = ENGINE.recommend(
                food_name=req.food_name,
                top_n=req.top_n,
                storage_type=req.storage_type,
                shelf_life_days=req.shelf_life_days,
                humidity=req.humidity,
                transport=req.transport,
                map_required=req.map_required,
            )
            results.append(result)
        except ValueError as exc:
            results.append({"food_name": req.food_name, "status": "error", "error": str(exc)})
    return {"count": len(results), "results": _json_safe(jsonable_encoder(results))}
