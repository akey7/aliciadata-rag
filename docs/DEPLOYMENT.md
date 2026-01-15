# Deployment

## Development

### Ensure dependencies are installed

- Install the `uv` Python package manager
- Ensure that PostgreSQL is insatlled and running.
- Ensure you have a HuggingFace account and an API key.

### Setup database

- **Setup a database user**: Create a database user for the RAG system.

- **Create the PostgreSQL DB**: Create a PostgreSQL database.

- **Execute migrations**: From pgAdmin or `psql`, execute the migrations on the newly created database in the following order:

```
migrations
├── 001_create_papers.sql
├── 002_create_chunks_papers.sql
├── 003_create_chunk_retrievals.sql
├── 004_create_rag_prompts.sql
└── 005_create_chunk_citations_view.sql
```

- **Ensure the DB user you just created has access**: Grant all permissions on all objects in your newly created PostgreSQL database with all these tables and views.

### Setup the environment

- **Create data folders**: In your home folder, *outside of the project repo*, create the following tree of subfolders in `~/aliciadata-rag`

```
.
├── crash_reports
├── input_md
├── md_storage
└── vectorstore
```

- **Create `.env`**: Copy `.env.example` to `.env` and replace the place holders with OpenAI API key, Anthropic API key, PostgreSQL credentials, and HuggingFace token. `KNOWLEDGE_AGENT_DATA_FOLDER` should point to the top level of the tree of folders you created above. `PAPER_SOURCE_FOLDER` should point to the `input_md` subfolder of the tree. 

- **Install Dependencies**: Dependencies are managed with `uv`. First, ensure `uv` is installed. After installation `conda deactivate` and conda environments (including base) that may be activated in your terminal. Then, from the root of the repo:

```
uv sync
```

### Starting Chroma

- **Start Chroma for ingestion**: Substitute `[KNOWLEDGE_AGENT_DATA_FOLDER]` for the root of the folders you created above.

- **Chroma needs to be started every time the app is executed**: For both ingestion and running the UI, Chroma needs to be running.

```
ANONYMIZED_TELEMETRY=False uv run chroma run --path [KNOWLEDGE_AGENT_DATA_FOLDER]/vectorstore
```

### Ingest the documents

- **Copy papers markdown files to `input_md`**: In my case, I have a corpus of 233 markdown-formatted scientific papers. These papers go in this folder.

- **Run the ingestion script**: Change into the repo's root folder. Execute the following command:

```
uv run ingest.py
```

If necessary, the AllenAI SPECTER model will be pulled from HuggingFace.

### Launching the app

- **Launch the Gradio app**: From the root of the repo, execute the following command:

```
uv run app.py
```
