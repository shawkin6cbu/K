# File: modules/pattern_extractor.py
import re

def extract_fields_from_text(text: str) -> dict:
    fields = {}

    # Sale Price
    match = re.search(r"Full Purchase Price \$?([0-9,]+\.\d{2})", text, re.IGNORECASE)
    if match:
        fields["SALEPRIC"] = match.group(1)

    # Earnest Money / Deposit
    match = re.search(r"Deposit (?:held by )?\$?([0-9,]+\.\d{2})", text, re.IGNORECASE)
    if match:
        fields["DEPOSIT"] = match.group(1)

    # Buyer Name
    match = re.search(r"BUYER(?:\(s\))?.*?called\s+(.*?)\s+whose address", text, re.IGNORECASE | re.DOTALL)
    if match:
        fields["BYR1NAM1"] = match.group(1).strip()

    # Buyer Address
    match = re.search(r"whose address.*?\n?([0-9]{3,5}.*?Drive|Street|Road|Ave)", text, re.IGNORECASE)
    if match:
        fields["BYR1ADR1"] = match.group(1).strip()

    # Property Address
    match = re.search(r"Address\s+(\d{2,5}.*?)\n", text, re.IGNORECASE)
    if match:
        fields["PROPSTRE"] = match.group(1).strip()

    return fields
