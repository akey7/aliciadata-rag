# BiologyRAG: PhD-Level Biology Research Q&A System
**Semantic search + LLM generation over 233 biology research papers from my PhD work**

🔗 [Live Demo](https://rag.aliciadata.com)

A production-oriented Retrieval-Augmented Generation (RAG) system designed to answer complex biology questions over a large, technical document corpus.

### Built to Demonstrate
- Domain-specific RAG implementation with scientific embeddings
- Deployed Python architecture with proper data persistence  
- End-to-end deployment from ingestion to live UI

### What's Working Well
- 233 papers successfully ingested and searchable  
- Multi-turn conversations with context retention  
- Consistent uptime on DigitalOcean
- Clean Gradio interface with chat and citations.
- Conversation history persistence in PostgreSQL 

## Architecture Highlights

### Design Decisions

- **Why SPECTER?** Pretrained on 700K+ scientific papers; semantic understanding of biology terminology
- **Why Markdown over PDF?** Cleaner structure, no table/figure extraction challenges, preserves formatting
- **Why single VPS?** Cost-effective for demo; all components colocated for minimal latency
- **Why no Docker?** Simplicity for initial deployment; containerization is planned enhancement

### Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Embeddings** | AllenAI SPECTER | Domain-specific for scientific papers (768-dimension) |
| **Vector Store** | ChromaDB | Persistent storage, lightweight, no external DB |
| **LLM** | OpenAI GPT-5 nano | Cost-efficient |
| **Orchestration** | LangChain | Standard RAG abstractions |
| **Conversation DB** | PostgreSQL | Tracks paper and chunk metadata, prompts |
| **Interface** | Gradio | Rapid prototyping, built-in chat UI |
| **Deployment** | DigitalOcean VPS | Predcitable monthly cost |

### Repository Structure

```
.
├── app.py                                            # Gradio frontend
├── .env.example                                      # .env template
├── docs                                              # Supplemental documentation
│   ├── ARCHITECTURE.md                               # Architecture overview
│   ├── DEPLOYMENT.md                                 # Dev/prod deployment
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

### More Details
More details about the architecture, including data flows during ingestion and chat, is in the [architecture document](docs/ARCHITECTURE.md).

## Deployment Highlights

More details about architecture, including dev and prod setup, is in the [deployment document](docs/DEPLOYMENT.md)

## Current Limitations

Current limitations include **lack of formal evals, context window management, concurrent user testing, containerization, and a smoother document update experience.** More details about a specific improvement roadmap is in the [roadmap document](docs/ROADMAP.md) and [evaluation document](docs/EVALUATION.md).
