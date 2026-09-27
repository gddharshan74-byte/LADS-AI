# PRISM AI
AI-Powered Risk Intelligence for MPLADS

Prototype v0.1 — project structure and demo dataset.

## Current goal
Build a working prototype that analyzes MPLADS-style project records, detects potential anomalies, and produces an explainable risk score for human review.

## Structure
- `backend/` — future FastAPI API and data services
- `ml/` — anomaly detection and risk-scoring logic
- `frontend/` — future React dashboard
- `docs/` — prototype notes

## Run the first data check

### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python ml/data_check.py
```

### Windows CMD
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python ml/data_check.py
```
