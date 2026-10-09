# GreenhouseIoT

IoT backend for greenhouse telemetry. Built step-by-step with FastAPI.

## Step 0 — run locally

```powershell
# 1. Create and activate venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install (editable + dev tools)
pip install -e ".[dev]"

# 3. Run API
uvicorn app.main:app --reload

# 4. Check health
# http://127.0.0.1:8000/api/v1/health
# Docs: http://127.0.0.1:8000/docs
```

## Quality gates

```powershell
ruff check .
pytest -v
```
