# aliciadata-rag
A RAG chat based on complex domain data from biology research.

## Starting Chroma

```
ANONYMIZED_TELEMETRY=False uv run chroma run --path [KNOWLEDGE_AGENT_DATA_FOLDER]/vectorstore
```

## Repository Structure

```
.
├── app.py                                              # Runs front-end Gradio app
├── ingest.py                                           # Ingests papers into the RAG system 
├── LICENSE                                             # MIT license
├── migrations                                          
│   ├── 001_create_papers.sql                           # Create papers table
│   ├── 002_create_chunks_papers.sql                    # Create mappings of chunks to papers
│   ├── 003_create_chunk_retrievals.sql                 # Create chunk retrieval tracking
│   ├── 004_create_rag_prompts.sql                      # Create prompt logging table
│   └── 005_create_chunk_citations_view.sql             # View for counting citations of chunks
├── prompts
│   ├── claude_categorization_system_prompt.mustache  # Categorization system prompt template for Haiku
│   ├── claude_categorization_user_prompt.mustache
│   └── openai_rag_system_prompt.mustache
├── pyproject.toml                                 
├── README.md
├── src
│   ├── agent_mixin.py
│   ├── category_workflow.py
│   ├── import_worker.py
│   ├── path_mixin.py
│   ├── rag_embeddings_workflow.py
│   └── worker_mixin.py
└── uv.lock
```
