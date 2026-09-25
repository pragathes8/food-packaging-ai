# Food Packaging AI — Integrated System v1.0

## Components

- `backend/` — FastAPI production API and validated recommendation engine
- `frontend/` — React + Vite user-facing recommendation application

## Runtime flow

Browser → React UI → FastAPI → FinalRecommendationPipelineV2 → requirement matching + deterministic evidence + ML enhancement + optimization → JSON → UI.

## Run

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The frontend defaults to `http://localhost:8000`.

For another backend URL:

```bash
VITE_API_BASE_URL=http://your-api-host:8000 npm run dev
```

## Validation status

Backend automated tests passed for health, metadata, food catalogue, packaging catalogue, recommendation generation, unknown-food handling and input validation.

The frontend source and package configuration are prepared for Vite. A full browser build requires running `npm install` in a normal Node environment; package installation was not used as part of this artifact-generation step.

## Scientific boundary

The application is evidence-guided decision support. It does not claim laboratory validation and does not fabricate unsupported OTR/WVTR/thickness thresholds, cost values, sustainability scores, or experimental shelf-life results.
