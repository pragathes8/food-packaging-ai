# PackSmart AI Frontend v1.0

React + Vite frontend for the Food Packaging AI Recommendation API.

## Features

- Food catalogue loaded from the API
- Storage, shelf-life, humidity and transport context
- MAP requirement toggle
- Ranked top-N packaging recommendations
- Compatibility, evidence coverage, optimization and ML signals
- Requirement-matching explanation
- Explicit evidence boundary in the UI

## Run

1. Start the API:
   `uvicorn app:app --reload --port 8000`

2. Install frontend dependencies:
   `npm install`

3. Start:
   `npm run dev`

The default API URL is `http://localhost:8000`.

For another API host, set:
`VITE_API_BASE_URL=http://your-api-host:8000`
