# Architecture

## Data Flows

### One-Time Ingestion
```
Research Papers (Markdown via Obsidian Web Clipper)
         ↓
MarkdownTextSplitter (3000 characters, 300 overlap)
         ↓
SPECTER Embeddings (768 dimensions)
         ↓
ChromaDB + PostgreSQL Persistent Storage 
```

### Chat at Runtime
```
User Query
    ↓
PostgreSQL (save prompt) 
    ↓
Chroma semantic search (top 15)
    ↓
GPT-5 nano
    ↓
Response to UI
```



