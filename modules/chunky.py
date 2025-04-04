import re
import tiktoken # Import tiktoken

# --- Constants for Token Chunking ---
# Target max tokens for the TEXT portion to leave room for the prompt
# (2048 total limit - ~700 prompt tokens = ~1348 available for text)
# Let's aim slightly lower for safety.
TARGET_MAX_TEXT_TOKENS = 1500
# Overlap between token-based chunks
OVERLAP_TOKENS = 100

def clean_and_chunk_contract_text_hybrid(full_text):
    """
    Cleans and chunks text using a hybrid approach:
    1. Initial cleaning.
    2. Structural splitting (based on numbered sections).
    3. Token-based splitting (with overlap) for any structural chunks
       that exceed the target token limit.

    Args:
        full_text (str): The complete text extracted from the contract PDF.

    Returns:
        list[str]: A list of cleaned text chunks, sized appropriately
                   for the LLM context window.
    """

    # --- 1. Initial Cleaning (Same as before) ---
    cleaned_text = re.sub(r"Docusign Envelope ID: [A-Z0-9\-]+\n?", "", full_text, flags=re.IGNORECASE)
    cleaned_text = re.sub(r"LEGACY NEW HOMES, LLC\n?", "", cleaned_text) # Example specific header
    cleaned_text = re.sub(r"Revised \d{2}/\d{2}/\d{2}\n?", "", cleaned_text)
    cleaned_text = re.sub(r"--- PAGE \d+ ---\n?", "", cleaned_text)
    cleaned_text = re.sub(r"-*[Dd]ocu[Ss]igned by:.*?\n", "", cleaned_text)
    cleaned_text = re.sub(r"[A-Z0-9]{10,}[.\s]*?\n", "", cleaned_text) # Attempt to remove signature hashes
    cleaned_text = re.sub(r"^\s*Initials:\s*(Seller)?\s*(Buyer\(s\))?[:\sA-Z]*\n", "", cleaned_text, flags=re.MULTILINE | re.IGNORECASE)
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text) # Replace multiple spaces/tabs with single space
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text) # Normalize paragraph breaks
    cleaned_text = re.sub(r'^\s+', '', cleaned_text) # Remove leading space
    cleaned_text = re.sub(r'"\s*([^"]+?)\s*\\n"\s*,\s*"([^"]+?)\\n"', r'\1: \2', cleaned_text) # Handle specific table format

    # --- 2. Structural Chunking (Same primary split as before) ---
    # Split primarily by numbered sections preceded by a double newline
    initial_chunks = re.split(r'\n\n(?=\d{1,2}\.\s+)', cleaned_text)

    # Refine initial chunks (simple merge of non-section starts)
    structural_chunks = []
    buffer = ""
    for chunk in initial_chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        # Check if chunk starts with a typical section marker
        if re.match(r"^\d{1,2}\.\s+", chunk):
            if buffer:
                structural_chunks.append(buffer)
            buffer = chunk # Start new buffer
        else:
            # Append to buffer if it doesn't start like a new section
            buffer += "\n\n" + chunk if buffer else chunk # Avoid leading newline if buffer empty

    if buffer: # Add the last buffered content
        structural_chunks.append(buffer)

    # Filter out very small structural chunks if desired (optional)
    structural_chunks = [chk for chk in structural_chunks if len(chk.split()) > 10]

    # --- 3. Token-Based Sub-Chunking (for oversized chunks) ---
    final_sized_chunks = []
    try:
        # Use OpenAI's tokenizer (good approximation for many models like Mistral)
        enc = tiktoken.get_encoding("cl100k_base")
    except Exception as e:
        print(f"❌ Error initializing tiktoken encoder: {e}")
        print("⚠️ Falling back to splitting oversized chunks by paragraph.")
        # Fallback strategy if tiktoken fails
        for struct_chunk in structural_chunks:
             if len(struct_chunk.split()) > TARGET_MAX_TEXT_TOKENS * 0.75: # Rough word count check
                  # Simple paragraph split as fallback
                  paragraphs = [p.strip() for p in struct_chunk.split('\n\n') if p.strip()]
                  current_chunk_text = ""
                  for p in paragraphs:
                       if len(current_chunk_text.split()) + len(p.split()) < TARGET_MAX_TEXT_TOKENS * 0.75:
                            current_chunk_text += ("\n\n" + p) if current_chunk_text else p
                       else:
                            if current_chunk_text:
                                 final_sized_chunks.append(current_chunk_text)
                            current_chunk_text = p # Start new chunk
                  if current_chunk_text: # Add last part
                       final_sized_chunks.append(current_chunk_text)
             else:
                  final_sized_chunks.append(struct_chunk) # Keep chunk as is
        return final_sized_chunks


    # Proceed with tiktoken chunking
    for struct_chunk in structural_chunks:
        tokens = enc.encode(struct_chunk)
        total_tokens = len(tokens)

        # If the structural chunk fits, keep it as is
        if total_tokens <= TARGET_MAX_TEXT_TOKENS:
            final_sized_chunks.append(struct_chunk)
            continue

        # If it's too large, apply token chunking with overlap
        print(f"ℹ️ Structural chunk too large ({total_tokens} tokens), applying token sub-chunking...")
        start = 0
        while start < total_tokens:
            end = min(start + TARGET_MAX_TEXT_TOKENS, total_tokens)
            chunk_tokens = tokens[start:end]

            # Decode carefully, handling potential errors
            try:
                chunk_text = enc.decode(chunk_tokens)
                final_sized_chunks.append(chunk_text.strip())
            except Exception as decode_err:
                 print(f"⚠️ Warning: Error decoding token sub-chunk: {decode_err}")
                 # Attempt to decode with error handling (might introduce replacement chars)
                 chunk_text = enc.decode(chunk_tokens, errors='replace')
                 final_sized_chunks.append(chunk_text.strip())


            # Move start position for the next chunk
            next_start = start + TARGET_MAX_TEXT_TOKENS - OVERLAP_TOKENS
            
            # Ensure we make progress and handle edge case near the end
            if next_start <= start:
                 next_start = start + 1 # Force progress if overlap is too large or chunk size too small
                 
            # If the next chunk would be identical to the current one due to overlap reaching the end
            if next_start >= total_tokens:
                 break # Avoid creating an identical final chunk
                 
            # Prevent creating a tiny last chunk if the overlap covers almost all remaining tokens
            if total_tokens - next_start < OVERLAP_TOKENS / 2 and end == total_tokens:
                 break # Don't make a tiny sliver chunk at the end

            start = next_start
            
            # Break if somehow start index goes beyond total tokens
            if start >= total_tokens:
                break


    # Final filter for any potentially empty chunks from processing
    return [chk for chk in final_sized_chunks if chk]

# --- How to use in main.py ---
# 1. Make sure you have tiktoken installed: pip install tiktoken
# 2. In main.py, change the import and function call:
#    from chunky import clean_and_chunk_contract_text_hybrid
#    ...
#    contract_chunks = clean_and_chunk_contract_text_hybrid(raw_text)
#    ...
#    print(f"\n🧠 Hybrid Chunks: {len(contract_chunks)}") # Update print statement
