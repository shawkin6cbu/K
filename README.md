KoobieKnaxx/                         # Project root directory
│
├── main.py                         # CLI entry point that orchestrates the full pipeline
├── requirements.txt                # Python dependencies (minimal for packaging)
├── config.py                       # Optional: settings like model path, chunk size, OCR toggle
├── README.md                       # Instructions for installation, usage, and build
│
├── /data/                          # Contract input/output files
│   ├── /input/                     # PDF files dropped by the user
│   ├── /output/                    # .pxt files generated from processed contracts
│
├── /models/                        # Local models used in LLM and Q&A
│   ├── mistral-7b.Q4_K_M.gguf      # Quantized LLM model (CPU-optimized, .gguf format)
│   └── embed_model/               # (Optional) Embedding model for Q&A (e.g., sentence-transformers)
│
├── /modules/                       # Core processing logic (each file is a pipeline stage)
│   ├── pdf_processor.py            # Extracts raw text from PDFs (supports OCR detection & fallback)
│   ├── text_cleaner.py             # Cleans and normalizes line breaks, hyphenation, etc.
│   ├── chunky.py                  # Breaks long contract text into safe, context-aware chunks
│   ├── llm_extractor.py            # Runs few-shot prompts against local LLM and returns structured fields
│   ├── file_writer.py              # Formats extracted fields into .pxt file and names it correctly
│
├── /qa/                            # (Future) Local Q&A engine module
│   ├── embedder.py                 # Generates embeddings for contract chunks (using local model)
│   ├── vector_store.py             # Stores and retrieves relevant chunks using FAISS
│   ├── question_answerer.py        # Composes context + question prompts for LLM-based answering
│
├── /gui/                           # (Future) Optional GUI frontend
│   ├── main_window.py              # Entry point for GUI drag-and-drop interface
│   └── style.qss                   # Optional: stylesheet for UI components
│
├── /tests/                         # Unit tests (modular)
│   ├── test_pdf_processor.py       # Tests for PDF extraction + OCR fallback
│   ├── test_llm_extractor.py       # Tests for field extraction correctness
│   └── test_file_writer.py         # Tests .pxt formatting and output
│
└── /bin/                           # (Optional) Compiled binaries or CLI launchers
    └── run.bat                     # Windows batch file for launching the app easily

