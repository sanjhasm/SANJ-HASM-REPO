\
from __future__ import annotations
import re
from typing import Dict, Any
from PIL import Image
import pytesseract, cv2
from .storage import load_config, load_patterns, upsert_supplier_patterns

def clean_val(s: str) -> str:
    return s.strip().strip(", #|=")

def pick(group, idx, default=""):
    try:
        return group[idx]
    except Exception:
        return default

def extract_with_patterns(text: str, pats: dict) -> Dict[str, str]:
    out = {"supplier":"", "invoice_no":"", "invoice_date":"", "invoice_amount":"", "full_text": text}
    # Supplier (always using default supplier pattern to discover name)
    sup_pat = pats["regex"]["supplier"]
    m_sup = re.search(sup_pat, text, flags=re.IGNORECASE)
    if m_sup:
        # group(2) may include rest-of-line; keep reasonable piece till newline
        val = clean_val(m_sup.group(2)).splitlines()[0]
        out["supplier"] = val

    # Determine supplier-specific overrides
    sp = load_patterns().get(out["supplier"] or "", {})
    invno_pat = sp.get("invno_pattern", pats["regex"]["invno"])
    invdt_pat = sp.get("invdt_pattern", pats["regex"]["invdt"])
    invamt_pat = sp.get("invamt_pattern", pats["regex"]["invamt"])

    m_no = re.search(invno_pat, text, flags=re.IGNORECASE)
    if m_no:
        out["invoice_no"] = clean_val(m_no.group(m_no.lastindex or 1))

    m_dt = re.search(invdt_pat, text, flags=re.IGNORECASE)
    if m_dt:
        out["invoice_date"] = clean_val(m_dt.group(m_dt.lastindex or 1))[:10]

    m_amt = re.search(invamt_pat, text, flags=re.IGNORECASE)
    if m_amt:
        out["invoice_amount"] = clean_val(m_amt.group(m_amt.lastindex or 1))

    # If supplier not in patterns, insert defaults to supplier_patterns.json
    if out["supplier"] and not sp:
        upsert_supplier_patterns(out["supplier"], pats["regex"]["invno"], pats["regex"]["invdt"], pats["regex"]["invamt"])

    return out

def ocr_and_extract(filepath: str) -> Dict[str, Any]:
    cfg = load_config()
    # point tesseract, if configured
    if cfg.get("tesseract_cmd"):
        pytesseract.pytesseract.tesseract_cmd = cfg["tesseract_cmd"]

    # Read image
    img = cv2.imread(filepath)
    if img is None:
        return {"supplier":"", "invoice_no":"", "invoice_date":"", "invoice_amount":"", "full_text":"", "error":"file not found"}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Light preprocessing (optional: blur/threshold if needed)
    text = pytesseract.image_to_string(gray)
    fields = extract_with_patterns(text, cfg)
    return fields
