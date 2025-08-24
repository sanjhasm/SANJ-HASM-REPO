\
from __future__ import annotations
import json, glob, datetime as dt
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
CONFIG_FILE = DATA_DIR / "config.json"
PATTERN_FILE = DATA_DIR / "supplier_patterns.json"

def ensure_dirs():
    for d in (DATA_DIR, UPLOAD_DIR):
        d.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps({
            "auth":{"username":"admin","password":"admin123"},
            "regex":{
                "supplier": r"(Sold\\s*By:|Supplier|Vendor|From)[:\\-]?\\s*(.*)",
                "invno": r"(Invoice\\s*Number|Invoice\\s*No|Bill\\s*No)[#\\:\\.\\s]*([A-Za-z0-9\\-\\/]+)",
                "invdt": r"(Invoice\\s*Date|Bill\\s*Date)[:\\-]?\\s*([0-9\\/\\-\\.\\sA-Za-z]+)",
                "invamt": r"(Grand\\s*Total|Net\\s*Amount|Total\\s*Amount)[:\\-]?\\s*(.*)"
            },
            "tesseract_cmd": r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            "tally":{"base_url":"","token":""}
        }, indent=2))
    if not PATTERN_FILE.exists():
        PATTERN_FILE.write_text(json.dumps({}, indent=2))

def load_config() -> dict:
    return json.loads(CONFIG_FILE.read_text())

def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

def load_patterns() -> dict:
    return json.loads(PATTERN_FILE.read_text())

def save_patterns(pats: dict):
    PATTERN_FILE.write_text(json.dumps(pats, indent=2))

def todays_file() -> Path:
    today = dt.date.today().strftime("%Y-%m-%d")
    return DATA_DIR / f"invoices-{today}.json"

def append_record(record: dict):
    f = todays_file()
    items = []
    if f.exists():
        items = json.loads(f.read_text())
    items.append(record)
    f.write_text(json.dumps(items, indent=2))

def aggregate_records() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for path in DATA_DIR.glob("invoices-*.json"):
        try:
            items.extend(json.loads(path.read_text()))
        except Exception:
            continue
    return items

def upsert_supplier_patterns(supplier: str, invno: str, invdt: str, invamt: str):
    pats = load_patterns()
    entry = pats.get(supplier, {})
    if invno: entry["invno_pattern"] = invno
    if invdt: entry["invdt_pattern"] = invdt
    if invamt: entry["invamt_pattern"] = invamt
    pats[supplier] = entry
    save_patterns(pats)
