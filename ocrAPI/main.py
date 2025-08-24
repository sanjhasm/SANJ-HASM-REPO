# pip install opencv-python
import cv2    

# pip install pytesseract
import pytesseract
import re       # regular expr
import json
import os

TEMPLATE_FILE = "supplier_templates.json"
def_supplier_pattern = r'(Sold\s*By:|Supplier|Vendor|From)[:\-]?\s*(.*)'
def_invno_pattern = r'(Invoice\s*Number|Invoice\s*No|Bill\s*No)[#\:\.\s]*([A-Za-z0-9\-\/]+)'
def_invdt_pattern = r'(Invoice\s*Date|Bill\s*Date)[:\-]?\s*([0-9\/\-\.\sA-Za-z]+)'
def_invamt_pattern = r'(Grand\s*Total|Net\s*Amount)[:\-]?\s*(.*)'

def load_templates():
    if os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_templates(templates):
    print(f"📌 Creating new Template as {templates}")
    with open(TEMPLATE_FILE, "w") as f:
        json.dump(templates, f, indent=2)

def extract_fields_from_image(fileName):
    # install tesseract engine from "https://github.com/UB-Mannheim/tesseract/wiki" and locate the installed path below
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    fields = {}
    supplier = None
    template = None
    pattern_invno = def_invno_pattern
    pattern_invdt = def_invdt_pattern
    pattern_invamt = def_invamt_pattern
    img = cv2.imread(fileName)

    # Convert to gray (optional for OCR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    imgToStr = pytesseract.image_to_string(gray)

    
    supplier_match = re.search(def_supplier_pattern, imgToStr, re.IGNORECASE)
    if supplier_match:
        supplier = supplier_match.group(2).strip(":, #|=")
        fields['supplier'] = supplier
        if supplier in templates:
            print(f"📌 Template found for Supplier '{supplier}'")
            template = templates[supplier]
            pattern_invno = template['invno_pattern']
            pattern_invdt = template['invdt_pattern']
            pattern_invamt = template['invamt_pattern']

    
    
    invoice_match = re.search(pattern_invno, imgToStr, re.IGNORECASE)
    if invoice_match:
        fields['inv_no'] = invoice_match.group(2).strip(", #|=")
    
    
    date_match = re.search(pattern_invdt, imgToStr, re.IGNORECASE)
    if date_match:
        fields['inv_date'] = date_match.group(2).strip(", #|=")[0:10]
    
    
    amount_match = re.search(pattern_invamt, imgToStr, re.IGNORECASE)
    if amount_match:
        fields['inv_amt'] = amount_match.group(2).strip(", #|=")
    
    if supplier and supplier not in templates:
        templates[supplier] = {
                "invno_pattern": def_invno_pattern,
                "invdt_pattern": def_invdt_pattern,
                "invamt_pattern": def_invamt_pattern
            }
        save_templates(templates)

    return fields, imgToStr



# Load templates
templates = load_templates()

print("--------------")
fields, imgToStr = extract_fields_from_image(r"invoices\inv-Flipkart.png")
print(fields)
print("--------------")
fields, imgToStr = extract_fields_from_image(r"invoices\inv-HomeCenter.png")
print(fields)
print("--------------")