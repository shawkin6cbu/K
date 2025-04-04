# File: modules/nuextract_phi3.py

from llama_cpp import Llama
import os
import re

# Path to your downloaded Phi-3 model
MODEL_PATH = os.path.join("models", "Phi-3-mini-4k-instruct-q4.gguf")

# Load model (once)
print("🧠 Loading Phi-3 model...")
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=4096,
    n_threads=os.cpu_count() or 4,
    verbose=False
)
print("✅ Phi-3 model ready.")

# Few-shot prompt prefix
PROMPT_TEMPLATE = """Extract specific fields from the contract text using FIELDNAME=value format.
Rules:
1. Only output lines for fields with values found in the text.
2. Adhere strictly to definitions and formats below.
3. For prices/deposits, include two decimal places (e.g., 100.00).
4. For phone numbers, use NUMBERS ONLY (no formatting).
5. For relevant addresses, use format: City, ST #####.

Definitions:
SETTDATE=Closing Date (MM/DD/YYYY)
COUNTY=The specific County name where the property is located (e.g., DeSoto). Check near property address details. Do not just use the state.
SALEPRIC=Contract sale price (Format: 123456.00)
DEPOSIT=Earnest Money Deposit (Format: 1234.00)
DEPHELD=Who holds deposit? Use exact option (Incoming Fund, Listing Agent, Seller, Settlement Agent, Office 1) OR the specific name found.

# Buyer Details - Pay close attention to separating Buyer 1 and Buyer 2
BYR1NAM1=Full name of the FIRST buyer listed.
BYR1REL1=Output 'and' ONLY if BYR1NAM2 has a value.
BYR1NAM2=Full name of the SECOND distinct buyer listed (if any). Omit line if no second buyer.
BYR1ADR1=Buyer 1 current street address only.
BYR1ADR2=Buyer 1 city, state, zip (Format: City, ST #####).
BYR1CELL1=Buyer 1 phone (NUMBERS ONLY).
BYR1EMAIL=Buyer 1 email.
BYR1CELL2=Buyer 2 phone (NUMBERS ONLY, if BYR1NAM2 found).
BYR1EMAIL2=Buyer 2 email (if BYR1NAM2 found).

# Seller Details - Pay close attention to separating Seller 1 and Seller 2
SLR1NAM1=Full name of the FIRST seller listed.
SLR1REL1=Output 'and' ONLY if SLR1NAM2 has a value.
SLR1NAM2=Full name of the SECOND distinct seller listed (if any). Omit line if no second seller.
SLR1ADR1=Seller 1 street address only.
SLR1ADR2=Seller 1 city, state, zip (Format: City, ST #####).
SLR1CELL1=Seller 1 phone (NUMBERS ONLY).
SLR1EMAIL=Seller 1 email.
SLR1CELL2=Seller 2 phone (NUMBERS ONLY, if SLR1NAM2 found).
SLR1EMAIL2=Seller 2 email (if SLR1NAM2 found).

# Property Details
PROPSTRE=Property street address (e.g., 673 Wells Drive).
LORU=Return "Lot" or "Unit" if number specified, otherwise omit.
LOTUNIT=Lot/Unit number only (e.g., 0074).
PROPCITY=Property City (e.g., Hernando).
STATELET=Property State (2-letter abbr, e.g., MS).
PROPZIP=Property zip code (e.g., 38632).
SUBDIVN=Property subdivision name.
PARCELID=Property parcel number (if specified).

# Agent Details (AG701=Listing/Seller, AG702=Selling/Buyer)
AG701NAM=Listing agent name.
AG701CONTLIC=Listing agent license #.
AG701FRM=Listing firm name.
AG701LIC=Listing firm license #.
AG701AD1=Listing firm street address.
AG701AD2=Listing firm city, state, zip (Format: City, ST #####).
AG701PH=Listing firm phone (NUMBERS ONLY).
AG701MO=Listing agent mobile (NUMBERS ONLY).
AG701EMAIL=Listing agent email.
AG702NAM=Selling agent name.
AG702CONTLIC=Selling agent license #.
AG702FRM=Selling firm name.
AG702LIC=Selling firm license #.
AG702AD1=Selling firm street address.
AG702AD2=Selling firm city, state, zip (Format: City, ST #####).
AG702PH=Selling firm phone (NUMBERS ONLY).
AG702MO=Selling agent mobile (NUMBERS ONLY).
AG702EMAIL=Selling agent email.

--- CONTRACT TEXT STARTS BELOW ---
{text}

--- FIELDS (only return lines with values):

"""

def extract_fields_from_chunk(chunk_text: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(text=chunk_text.strip())


    try:
        output = llm(prompt, max_tokens=512, stop=["Answer:"], echo=False)
        result = output["choices"][0]["text"].strip()
    except Exception as e:
        print(f"❌ LLM error: {e}")
        return {}

    # Extract FIELD=VALUE pairs from output
    fields = {}
    for line in result.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            fields[key.strip()] = value.strip()

    return fields
