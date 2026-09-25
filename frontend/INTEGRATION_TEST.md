# End-to-end integration test plan

1. Start API:
   `uvicorn app:app --reload --port 8000`

2. Start frontend:
   `npm install`
   `npm run dev`

3. Open:
   `http://localhost:5173`

4. Select `Tomato`, keep the default conditions, and click **Generate recommendations**.

5. Expected:
   - API status becomes **Engine online**
   - recommendation status is returned
   - 3 packaging recommendations appear
   - selecting a recommendation reveals scores, evidence coverage and explanation

The backend API test suite is automated in `../Food_Packaging_AI_API_v1/test_api.py`.
