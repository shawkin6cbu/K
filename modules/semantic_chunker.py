from llama_cpp import Llama

# Load your model (tune n_ctx & n_threads as needed)
llm = Llama(
    model_path="models/Mistral-7B-Instruct-v0.3.Q4_K_M.gguf",
    n_ctx=2048,
    n_threads=6
)

# Prompt for semantic chunking
CHUNKING_PROMPT_TEMPLATE = """
You are a contract processor. Split the legal contract text below into logical sections.
Use this format:

SECTION: [Section Title]
[Section Text]

Example titles:
- Buyer Information
- Seller Information
- Purchase Price
- Deposit
- Property Description
- Closing
- Possession
- Agents
- Commission
- Other

Return only clearly divided sections. Keep text readable and unbroken.

Text:
{text}
"""

def semantic_chunk_contract(cleaned_text):
    prompt = CHUNKING_PROMPT_TEMPLATE.format(text=cleaned_text.strip())

    response = llm(prompt, max_tokens=1024, stop=["SECTION: Other"])
    raw_output = response["choices"][0]["text"].strip()

    return parse_sections(raw_output)

def parse_sections(llm_output):
    sections = []
    current_section = ""
    lines = llm_output.splitlines()

    for line in lines:
        if line.strip().startswith("SECTION:"):
            if current_section:
                sections.append(current_section.strip())
                current_section = ""
        current_section += line + "\n"

    if current_section:
        sections.append(current_section.strip())

    return sections
