from llama_cpp import Llama
import re
import os # For potential future path joining

# --- Configuration ---
# Consider using environment variables or a config file in a real application
MODEL_FILENAME = "Mistral-7B-Instruct-v0.3.Q4_K_M.gguf"
MODELS_DIR = "models" # Assuming models are in a 'models' subdirectory
MODEL_PATH = os.path.join(MODELS_DIR, MODEL_FILENAME)

N_CTX = 2048
N_THREADS = 6 # Adjust to your CPU core count
MAX_OUTPUT_TOKENS = 96 # Increased max tokens for output

# Define expected fields explicitly for better parsing/validation
EXPECTED_FIELDS = [
    "SETTDATE", "COUNTY", "SALEPRIC", "DEPOSIT",
    "DEPHELD", "BYR1NAM1", "BYR1REL1", "BYR1NAM2",
    "BYR1ADR1", "BYR1ADR2", "BYR1CELL1", "BYR1EMAIL", "BYR1CELL2", "BYR1EMAIL2",
    "SLR1NAM1", "SLR1REL1", "SLR1NAM2", "SLR1ADR1", "SLR1ADR2", "SLR1CELL1",
    "SLR1EMAIL", "SLR1CELL2", "SLR1EMAIL2", "PROPSTRE", "LORU", "LOTUNIT",
    "PROPCITY", "CITYCODE", "STATELET", "PROPZIP", "SUBDIVN", "PARCELID",
    "AG701NAM", "AG701CONTLIC", "AG701FRM", "AG701LIC", "AG701AD1", "AG701AD2",
    "AG701PH", "AG701MO", "AG701EMAIL", "AG702NAM", "AG702CONTLIC", "AG702FRM",
    "AG702LIC", "AG702AD1", "AG702AD2", "AG702PH", "AG702MO", "AG702EMAIL"
]
# --- End Configuration ---

# --- Model Loading ---
# Consider lazy loading if this module is part of a larger app
try:
    print(f"🌀 Loading model from: {MODEL_PATH}...")
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=N_CTX,
        n_threads=N_THREADS,
        verbose=False # Set to True for more detailed llama.cpp output
    )
    print("✅ Model loaded successfully.")
except Exception as e:
    print(f"❌❌❌ Fatal Error: Could not load model from {MODEL_PATH}")
    print(f"Error details: {e}")
    # Depending on your application structure, you might raise the exception
    # or exit here if the model is essential.
    llm = None # Ensure llm is None if loading failed
# --- End Model Loading ---


# --- Prompt Template ---
# No changes needed here, it's quite detailed.
PROMPT_TEMPLATE = """
Extract specific fields from the contract text using FIELDNAME=value format.
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
# --- End Prompt Template ---


def extract_fields_from_chunk(chunk_text):
    """Formats prompt, calls LLM, and parses output for a single chunk."""
    if llm is None:
        print("❌ LLM not loaded. Cannot extract fields.")
        return {} # Return empty dict if model loading failed

    prompt = PROMPT_TEMPLATE.format(text=chunk_text.strip())

    try:
        response = llm(
            prompt,
            max_tokens=MAX_OUTPUT_TOKENS,
            stop=["\n\n", "---", "Fields:"], # Added "---" as a potential stop
            echo=False # Don't repeat the prompt in the output
        )
        raw_output = response["choices"][0]["text"].strip()
        # print(f"--- Raw LLM Output ---\n{raw_output}\n----------------------") # Uncomment for debugging
        return parse_output(raw_output)
    except Exception as e:
        print(f"❌ Error during LLM call or processing: {e}")
        # Optionally log the chunk_text or prompt that caused the error
        return {} # Return empty dict on error


def parse_output(output_text):
    """Parses the 'FIELD=value' lines from the LLM output."""
    fields = {}
    lines = output_text.splitlines()
    for line in lines:
        line = line.strip()
        if not line or "=" not in line: # Skip empty lines or lines without '='
            continue

        key, value = line.split("=", 1) # Split only on the first '='
        key = key.strip()
        value = value.strip()

        # Optional: Validate if the key is one we expect
        if key in EXPECTED_FIELDS:
            if value: # Only add if value is not empty
                 fields[key] = value
        # else: # Uncomment below to log unexpected keys from the LLM
        #    print(f"⚠️ LLM returned unexpected key: '{key}'")

    return fields