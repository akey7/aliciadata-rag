CREATE TABLE IF NOT EXISTS chunks_papers (
   id SERIAL PRIMARY KEY,
   chunk TEXT,
   paper_uuid4 VARCHAR(40)
);
