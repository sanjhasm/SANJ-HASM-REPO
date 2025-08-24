\
from __future__ import annotations
import os, json, uuid, datetime as dt
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .storage import (
    DATA_DIR, UPLOAD_DIR, CONFIG_FILE, PATTERN_FILE,
    load_config, save_config, ensure_dirs, aggregate_records,
    append_record, load_patterns, upsert_supplier_patterns
)
from .auth import require_user, check_login
from .ocr import ocr_and_extract
from .tally import send_all_to_tally

app = FastAPI(title="FastAPI OCR Purchase Bills")
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("APP_SESSION_SECRET", "please-change-me"), same_site="lax")

# Ensure dirs and default config
ensure_dirs()

# Static & templates
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "static")), name="static")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

# ---------------- Routes: Auth ----------------

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    cfg = load_config()
    if check_login(username, password, cfg):
        request.session["user"] = {"name": username}
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

# ---------------- Pages ----------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request, user=Depends(require_user)):
    return templates.TemplateResponse("home.html", {"request": request, "title": "Home"})

@app.get("/activities", response_class=HTMLResponse)
def activities(request: Request, user=Depends(require_user)):
    return templates.TemplateResponse("activities.html", {"request": request, "title": "Activities"})

@app.get("/activities/scan-bills", response_class=HTMLResponse)
def scan_bills(request: Request, user=Depends(require_user)):
    return templates.TemplateResponse("scan_bills.html", {"request": request, "title": "Scan Purchase Bills"})

@app.get("/grid", response_class=HTMLResponse)
def grid_page(request: Request, user=Depends(require_user)):
    return templates.TemplateResponse("grid.html", {"request": request, "title": "Grid"})

@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, user=Depends(require_user)):
    cfg = load_config()
    return templates.TemplateResponse("settings.html", {"request": request, "title": "Settings", **cfg})

# ---------------- APIs ----------------

@app.post("/api/ocr")
async def api_ocr(request: Request, user=Depends(require_user), files: List[UploadFile] = File(...)):
    items = []
    for f in files:
        # Save upload
        dst = UPLOAD_DIR / f.filename
        content = await f.read()
        with open(dst, "wb") as out:
            out.write(content)

        # OCR + extract
        fields = ocr_and_extract(str(dst))
        fields["source_file"] = f.filename
        items.append(fields)
    return {"items": items}

@app.post("/api/confirm")
async def api_confirm(payload: Dict[str, Any], user=Depends(require_user)):
    record = {
        "id": str(uuid.uuid4()),
        "supplier": payload.get("supplier", ""),
        "invoice_no": payload.get("invoice_no", ""),
        "invoice_date": payload.get("invoice_date", ""),
        "invoice_amount": payload.get("invoice_amount", ""),
        "full_text": payload.get("full_text", ""),
        "source_file": payload.get("source_file", ""),
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
        "sent_to_tally": "No"
    }
    append_record(record)
    return {"ok": True, "id": record["id"]}

@app.get("/api/grid")
def api_grid(user=Depends(require_user)):
    items = aggregate_records()
    return {"items": items}

@app.post("/api/tally/send-all")
def api_tally_send_all(user=Depends(require_user)):
    sent, failed = send_all_to_tally()
    return {"sent": sent, "failed": failed}

@app.get("/api/config")
def api_get_config(user=Depends(require_user)):
    return load_config()

@app.post("/api/config")
def api_save_config(payload: Dict[str, Any], user=Depends(require_user)):
    cfg = load_config()
    cfg.update(payload)
    save_config(cfg)
    return {"ok": True}

@app.get("/api/patterns")
def api_get_patterns(user=Depends(require_user)):
    return load_patterns()

@app.post("/api/patterns")
def api_upsert_patterns(payload: Dict[str, Any], user=Depends(require_user)):
    supplier = payload.get("supplier", "").strip()
    invno = payload.get("invno_pattern", "")
    invdt = payload.get("invdt_pattern", "")
    invamt = payload.get("invamt_pattern", "")
    if not supplier:
        return JSONResponse({"ok": False, "error": "supplier required"}, status_code=400)
    upsert_supplier_patterns(supplier, invno, invdt, invamt)
    return {"ok": True}
