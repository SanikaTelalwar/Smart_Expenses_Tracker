# utils/ocr.py
import pytesseract
from PIL import Image
import io
import re
from datetime import datetime

# If tesseract is not in PATH, set it explicitly
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def ocr_image_to_text(file_bytes):
    image = Image.open(io.BytesIO(file_bytes))
    text = pytesseract.image_to_string(image)
    return text

import re

def parse_receipt_text(text):
    """
    Extract vendor, date, and total amount in INR from OCR text.
    """
    result = {"vendor": None, "date": None, "total": None}

    lines = text.split("\n")
    lines = [line.strip() for line in lines if line.strip()]

    if lines:
        result["vendor"] = lines[0]  # usually first line

    # Look for date patterns (dd/mm/yyyy)
    date_match = re.search(r"\d{2}/\d{2}/\d{4}", text)
    if date_match:
        result["date"] = date_match.group()

    # Look for amounts with ₹, Rs, INR
    amounts = []
    for line in lines:
        match = re.findall(r"(?:₹|Rs\.?|INR)\s?(\d+(?:\.\d{1,2})?)", line)
        if match:
            amounts += [float(x) for x in match]

    # Fallback: pick largest number if no ₹ found
    if not amounts:
        numbers = re.findall(r"\d+(?:\.\d{1,2})?", text)
        if numbers:
            amounts = [float(n) for n in numbers]

    if amounts:
        result["total"] = max(amounts)  # assume largest is total

    return result
