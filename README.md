# aliciadata-rag
A RAG chat based on complex domain data from biology research.

## Starting Chroma

```
ANONYMIZED_TELEMETRY=False uv run chroma run --path [KNOWLEDGE_AGENT_DATA_FOLDER]/vectorstore
```

## Repository Structure

```
.
├── app.py                                            # Gradio frontend
├── docs                                              # Supplemental documentation
│   ├── ARCHITECTURE.md                               # Architecture overview
│   ├── EVALUATION.md                                 # Future plan for evals
│   └── ROADMAP.md                                    # Roadmap of future features
├── ingest.py                                         # Paper ingestion pipeline
├── LICENSE                                           # MIT license
├── migrations                                        # SQL-based PostgreSQL migraitons
│   ├── 001_create_papers.sql                         # Tracks papers and metadata
│   ├── 002_create_chunks_papers.sql                  # Tracks chunks of papers
│   ├── 003_create_chunk_retrievals.sql               # Tracks retrievals of chunks
│   ├── 004_create_rag_prompts.sql                    # Logs prompts that start chats
│   └── 005_create_chunk_citations_view.sql           # Tracks citations counts of chunks
├── prompts                                           # Templates to generate prompts
│   ├── claude_categorization_system_prompt.mustache  # Categorization system prompt template
│   ├── claude_categorization_user_prompt.mustache    # Categorization user prompt template 
│   └── openai_rag_system_prompt.mustache             # RAG chat system prompt template
├── pyproject.toml                                    # Dependency and project management
├── README.md                                         # This README
├── src                                               # Modules for app and ingestion
│   ├── agent_mixin.py                                # Connections to OpenAI, Anthropic
│   ├── category_workflow.py                          # Categorization of papers with Antrhopic
│   ├── import_worker.py                              # Imports markdown papers into the system
│   ├── path_mixin.py                                 # Manages file system paths
│   ├── rag_embeddings_workflow.py                    # Handles semantic storage and retrieval
│   └── worker_mixin.py                               # Mostly handles PostgreSQL connectivity
└── uv.lock                                           # Exact dependency versions.
```
