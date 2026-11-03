# TurbineOpt POC

Executive-facing proof of concept for a Combined Cycle Optimization Agent for jet-powered AI data centers.

The product story is simple: TurbineOpt does not sell AI. It reduces fuel cost. If the optimizer does not save money, the customer does not pay.

## What Is Included

- Python FastAPI backend with deterministic combined-cycle simulation.
- Google ADK-ready agent orchestration layer with local fallback outputs.
- React + Vite + TypeScript dashboard for executive demos.
- Synthetic plant state, baseline, and scenario data.
- Backend tests for savings, dispatch, maintenance risk, and fallback behavior.

## Run Locally

### Backend

```powershell
cd backend
python -m venv py313venv
.\py313venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn turbineopt.api.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL, usually `http://localhost:5173`.

## API

- `GET /api/plant-state`
- `GET /api/baseline`
- `GET /api/agents/status`
- `POST /api/scenario/optimize`

The POC is advisory only. Recommendations require operator approval and do not perform automated plant control.

## Gemini / Vertex AI Credentials

The app can use Google Cloud Application Default Credentials instead of an API key.

1. Authenticate locally:

```powershell
gcloud auth application-default login
```

2. Edit `.env`:

```powershell
GOOGLE_CLOUD_PROJECT=your-google-cloud-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true
TURBINEOPT_ADK_MODEL=gemini-3.5-flash
```

3. Restart the backend.

Use the Google Cloud project ID, not only the project display name.
