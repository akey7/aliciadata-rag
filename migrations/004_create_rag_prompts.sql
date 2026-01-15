-- Tracks the first prompts that start RAG chats.

CREATE TABLE rag_prompts (
   id SERIAL PRIMARY KEY,
   prompt TEXT,
   datetime_prompted TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
