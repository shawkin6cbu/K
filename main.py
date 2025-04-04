import os
import time

from config import MODEL_MODE
from modules.pdf_processor import extract_contract_text
from modules.chunky import clean_and_chunk_contract_text_hybrid as chunk_text
from modules.pattern_extractor import extract_fields_from_text as extract_by_pattern

# Load Phi-3 only if needed
if MODEL_MODE == "phi3":
    from modules.nuextract_phi3 import extract_fields_from_chunk as extract_by_llm
else:
    from modules.llm_extractor import extract_fields_from_chunk as extract_by_llm

PDF_PATH = r"C:\Users\shawk\OneDrive\Desktop\KoobieKnaxx\data\input\Byrd Contract.pdf"

def format_time(seconds):
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins}m {secs}s"

def main():
    if not os.path.exists(PDF_PATH):
        print(f"❌ File not found: {PDF_PATH}")
        return

    print(f"📥 Processing: {PDF_PATH}")
    raw_text, was_scanned = extract_contract_text(PDF_PATH)

    if not raw_text.strip():
        print("❌ No text extracted.")
        return

    # Step 1: Pattern-based extraction
    pattern_fields = extract_by_pattern(raw_text)
    print(f"✅ Pattern-based fields extracted: {len(pattern_fields)}")

    # Step 2: Chunk text
    chunks = chunk_text(raw_text)
    print(f"✂️ Text split into {len(chunks)} smart chunks")

    # Step 3: Fallback LLM only for missing fields
    all_fields = pattern_fields.copy()
    total_time = 0

    for i, chunk in enumerate(chunks):
        needed_fields = [key for key in REQUIRED_FIELDS if key not in all_fields or not all_fields[key]]
        if not needed_fields:
            break  # All required fields found, skip remaining chunks

        chunk_start = time.time()
        print(f"\n🧠 Extracting from chunk {i+1}/{len(chunks)} (LLM fallback)...")

        extracted = extract_by_llm(chunk)

        for key in needed_fields:
            if key in extracted and extracted[key] and key not in all_fields:
                all_fields[key] = extracted[key]

        chunk_end = time.time()
        total_time += chunk_end - chunk_start

        avg_time = total_time / (i + 1)
        remaining = avg_time * (len(chunks) - (i + 1))
        print(f"   ⏳ Chunk processed in {chunk_end - chunk_start:.2f}s — Est. left: {format_time(remaining)}")

    print("\n✅ Final Extracted Fields:")
    print("-" * 40)
    for key in sorted(all_fields):
        print(f"{key} = {all_fields[key]}")

if __name__ == "__main__":
    # Minimal list of known field codes — expand as needed
    REQUIRED_FIELDS = [
        "SETTDATE", "SALEPRIC", "DEPOSIT", "DEPHELD", "BYR1NAM1",
        "BYR1ADR1", "PROPSTRE", "PROPZIP", "COUNTY", "STATELET"
    ]

    start = time.time()
    main()
    end = time.time()
    print(f"\n⏱ Total runtime: {format_time(end - start)}")
