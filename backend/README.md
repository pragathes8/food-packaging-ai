# Food Packaging AI Recommendation API v1.0

Production-facing API wrapper around the integrated Food Packaging AI engine.

## Architecture

Client → FastAPI → FinalRecommendationPipelineV2 → requirement matching + deterministic evidence + ML enhancement + optimization → explainable recommendation.

## Endpoints

- `GET /health` — service health
- `GET /metadata` — engine coverage metadata
- `GET /foods` — supported food catalogue
- `GET /packaging` — packaging catalogue
- `POST /recommend` — single recommendation request
- `POST /recommend/batch` — up to 50 recommendation requests

## Run locally

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

Then open `/docs` for the interactive OpenAPI UI.

## Example request

```json
{
  "food_name": "Tomato",
  "top_n": 3,
  "storage_type": "Refrigerated",
  "shelf_life_days": 10,
  "humidity": "High",
  "transport": "Cold chain",
  "map_required": false
}
```

## Important model boundary

The API exposes the evidence-guided recommendation engine. It does not claim laboratory validation, and it does not fabricate OTR/WVTR/thickness thresholds, cost values, sustainability scores, or experimental shelf-life results when those are not supported by the supplied project data.
