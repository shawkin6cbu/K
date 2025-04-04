import re

def clean_text(raw_text: str) -> str:
    """
    Cleans and normalizes contract text.
    Fixes line breaks, hyphenation, and extra whitespace.
    """
    # Remove hyphenated line breaks (e.g. "infor-\nmation" → "information")
    cleaned = re.sub(r"-\n", "", raw_text)

    # Replace line breaks within paragraphs with spaces
    cleaned = re.sub(r"(?<!\n)\n(?!\n)", " ", cleaned)

    # Normalize double/triple newlines to paragraph breaks
    cleaned = re.sub(r"\n{2,}", "\n\n", cleaned)

    # Remove excessive spaces
    cleaned = re.sub(r" {2,}", " ", cleaned)

    return cleaned.strip()
