# FastAPI OCR Purchase Bills (No DB)

A production-ready scaffold that scans purchase bill images, OCRs them with Tesseract, extracts key fields using regex, and persists results to date-wise JSON files. It also maintains supplier-specific regex patterns and lets you send aggregated grid data to a (mock) Tally API.

## Features
- FastAPI + Jinja2 UI (no DB; JSON storage)
- Simple session login (hardcoded creds in config)
- Upload images, OCR, extract: Supplier, Invoice No, Date, Amount
- Supplier-specific regex patterns file (auto-grows)
- Grid view across all date JSONs
- Send-All-to-Tally mock (marks flag in files)
- Minimal, clean CSS included
- Dockerfile included

## Install
```bash
python -m venv .venv
. .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
```

## Tesseract
Install the Tesseract OCR engine:
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`

Update the `tesseract_cmd` path in `data/config.json` if needed.

## Run
```bash
uvicorn app.main:app --reload --port 8000
```
Open http://127.0.0.1:8000/login


## Build & Run with Docker
```bash
docker build -t fastapi-ocr-bills .
docker run -p 8000:8000 -v $(pwd)/data:/app/data -v $(pwd)/uploads:/app/uploads fastapi-ocr-bills
```

