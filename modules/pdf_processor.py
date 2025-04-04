# File: modules/pdf_processor.py
# Purpose: Drop-in OCR + direct extraction module for KoobieNaxx
# Uses parallel OCR if digital text is insufficient

import pytesseract
from pdf2image import convert_from_path
import fitz  # PyMuPDF
import os
import concurrent.futures
import time

# Optional: specify Tesseract path here if needed
TESSERACT_CMD = None  # e.g., r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- Internal: Page-level OCR worker (runs in thread) ---
def _ocr_page_worker(image):
    try:
        return pytesseract.image_to_string(image, lang='eng')
    except pytesseract.TesseractNotFoundError:
        return "TESSERACT_NOT_FOUND"
    except Exception:
        return None

# --- Attempt direct text extraction (fast path) ---
def _attempt_direct(pdf_path, min_text_per_page=50):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text += page.get_text() + f"\n\n--- Page {page_num + 1} End (Direct) ---\n\n"
        doc.close()
        avg_chars = len(text.strip()) / max(1, doc.page_count)
        return text.strip() if avg_chars > min_text_per_page else None
    except:
        return None

# --- Perform threaded OCR if needed ---
def _perform_threaded_ocr(pdf_path):
    if TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

    try:
        print("🧠 Performing OCR with thread-level parallelism...")
        images = convert_from_path(pdf_path, thread_count=max(1, os.cpu_count() // 2))
        num_pages = len(images)
        print(f"🖼️ Converted {num_pages} pages to images. Starting OCR...")

        final_text = ""
        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            results = list(executor.map(_ocr_page_worker, images))

        for i, result in enumerate(results):
            if result == "TESSERACT_NOT_FOUND":
                print("❌ Tesseract not found. Ensure it's installed or set TESSERACT_CMD.")
                return None
            elif result is None:
                final_text += f"\n\n--- ERROR OCRing Page {i+1} ---\n\n"
            else:
                final_text += result + f"\n\n--- Page {i+1} End (OCR) ---\n\n"

        return final_text.strip()

    except Exception as e:
        print(f"❌ OCR error: {e}")
        return None

# --- Main KoobieNaxx Interface Function ---
def extract_contract_text(pdf_path):
    """
    Tries direct text extraction, falls back to OCR if needed.
    Returns:
        (str: extracted_text, bool: used_ocr)
    """
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return "", False

    print("📄 Trying digital text extraction...")
    direct_text = _attempt_direct(pdf_path)
    if direct_text:
        print("✅ Successfully extracted digital text.")
        return direct_text, False

    print("🔍 Digital extraction too weak. Switching to OCR...")
    ocr_text = _perform_threaded_ocr(pdf_path)
    if ocr_text:
        print("✅ OCR succeeded.")
        return ocr_text, True

    print("❌ OCR failed. No usable text extracted.")
    return "", True
