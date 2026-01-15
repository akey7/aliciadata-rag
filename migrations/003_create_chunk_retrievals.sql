-- Tracks how many times chunks are retrieved in chats.

CREATE TABLE chunk_retrievals (
   id SERIAL PRIMARY KEY,
   chunk_id INTEGER REFERENCES chunks_papers(id),
   datetime_retrieved TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
