# File: modules/section_extractor.py
import fitz # Still potentially useful for other helper funcs, but not core logic now
import re
import os

# --- Configuration: Define High-Value Section Markers ---
# Customize this list based on your contracts
HIGH_VALUE_HEADING_PATTERNS = [
    re.compile(r"^\s*\d{1,2}\.\s*Parties\b", re.IGNORECASE),
    re.compile(r"^\s*\d{1,2}\.\s*Buyer\(s\)\b", re.IGNORECASE),
    re.compile(r"^\s*\d{1,2}\.\s*Seller\(s\)\b", re.IGNORECASE),
    re.compile(r"^\s*\d{1,2}\.\s*Property\b", re.IGNORECASE),
    re.compile(r"^\s*\d{1,2}\.\s*Purchase Price\b", re.IGNORECASE),
    re.compile(r"^\s*\d{1,2}\.\s*Financial Terms\b", re.IGNORECASE),
    re.compile(r"^\s*\d{1,2}\.\s*Deposit\b", re.IGNORECASE),
    re.compile(r"^\s*\d{1,2}\.\s*Closing Date\b", re.IGNORECASE),
    re.compile(r"^\s*\d{1,2}\.\s*Settlement\b", re.IGNORECASE),
    re.compile(r"^\s*\d{1,2}\.\s*Agency Disclosure\b", re.IGNORECASE),
    re.compile(r"^\s*ADDENDUM\s*#[A-Z]\b", re.IGNORECASE),
    re.compile(r"^\s*CONTRACT ADDENDUM\b", re.IGNORECASE)
]

# General pattern to identify ANY potential heading (used for splitting)
ANY_HEADING_PATTERN_FOR_SPLIT = re.compile(
    r"^\s*(?:\d{1,2}\.\s+|PARTIES|PROPERTY|PURCHASE PRICE|FINANCING|DEPOSIT|CLOSING|SETTLEMENT|AGENCY DISCLOSURE|WARRANTIES|CONTINGENCIES|ADDENDUM)\b",
    re.IGNORECASE
)
# --- End Configuration ---


def is_high_value_heading(line_text):
    """Check if a line matches one of the specific high-value patterns."""
    # Simple check against the high-value list
    for pattern in HIGH_VALUE_HEADING_PATTERNS:
        if pattern.match(line_text):
            return True
    # Addenda are generally high value
    if re.match(r"^\s*(ADDENDUM|CONTRACT ADDENDUM)\b", line_text, re.IGNORECASE):
         return True
    return False


def extract_high_value_sections(full_text):
    """
    Extracts text only from predefined "high-value" sections using regex splitting.
    NOTE: This version takes text input and relies purely on regex matching of headings.

    Args:
        full_text (str): The complete text extracted from the contract.

    Returns:
        str: Concatenated text from high-value sections, or empty string on error.
    """
    if not full_text:
        return ""

    relevant_text_parts = []
    # Split the document roughly by potential headings to get candidate sections
    # Use a lookahead (?=...) in split to keep the delimiter (heading) with the following text
    potential_sections = re.split(f"({ANY_HEADING_PATTERN_FOR_SPLIT.pattern})", full_text, flags=re.MULTILINE | re.IGNORECASE)

    # The first chunk might not start with a heading, check if page 1 content is relevant
    # A simple heuristic: always include the first part if it looks substantial
    # Or rely on the ALWAYS_INCLUDE_FIRST_N_PAGES in main.py if preferred
    # For simplicity here, let's check if the *first heading* is high-value

    current_section_is_high_value = False
    accumulated_text = ""

    # Iterate through parts: heading1, content1, heading2, content2...
    # (re.split with capturing group returns list like: [before_first_match, delimiter1, after_delimiter1, delimiter2, after_delimiter2...])
    
    # Handle text before the first potential heading match
    if potential_sections[0].strip():
        # Decide if the first block (likely page 1 content) should always be included
        # Let's assume YES for now, as key details are often there. Adjust if needed.
        relevant_text_parts.append(potential_sections[0].strip())
        # print(f"DEBUG: Including initial block.") # Debug

    # Process the rest (heading followed by content)
    for i in range(1, len(potential_sections), 2): # Step by 2: grab heading and its content
        heading = potential_sections[i].strip() if i < len(potential_sections) else ""
        content = potential_sections[i+1].strip() if (i+1) < len(potential_sections) else ""

        if heading:
            # Check if this heading marks a high-value section
            if is_high_value_heading(heading):
                 # print(f"DEBUG: Found High-Value Section: {heading[:50]}") # Debug
                 relevant_text_parts.append(heading) # Add the heading
                 if content: relevant_text_parts.append(content) # Add the content
            # else: # Debug
                 # print(f"DEBUG: Skipping Section: {heading[:50]}") # Debug


    # Join the relevant parts
    final_text = "\n\n".join(relevant_text_parts).strip()
    # Final cleanup
    final_text = re.sub(r'\n{3,}', '\n\n', final_text)

    return final_text

# --- Example Usage (Optional - for testing this file directly) ---
if __name__ == "__main__":
    # This requires pdf_processor.py in the *same directory* or modifying imports
    # It's better to test this via main.py now
    print("Please test this module via main.py")
    # Example:
    # from pdf_processor import extract_contract_text # Assumes in same dir
    # pdf_file = r"C:\path\to\your\Abeja Contract2.pdf"
    # raw_text, was_scanned = extract_contract_text(pdf_file)
    # if not was_scanned:
    #     extracted = extract_high_value_sections(raw_text)
    #     print(extracted[:1000])