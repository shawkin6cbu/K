import tiktoken

def token_chunk_text(text, max_tokens=500, overlap=100):
    """
    Tokenizes the text and chunks it into LLM-friendly segments
    using token counts (with overlap).
    """
    # Use OpenAI's tokenizer (good approximation for Mistral)
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)

    chunks = []
    start = 0

    while start < len(tokens):
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
        start += max_tokens - overlap  # slide with overlap

    return chunks
