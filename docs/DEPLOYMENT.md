# Deployment

## Development

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

### Ingest the documents

### Launching the app on development

#### Starting Chroma

```
ANONYMIZED_TELEMETRY=False uv run chroma run --path [KNOWLEDGE_AGENT_DATA_FOLDER]/vectorstore
```
