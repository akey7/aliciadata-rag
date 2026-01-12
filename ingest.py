import os

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
import logging
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
from huggingface_hub import login
from sentence_transformers import SentenceTransformer
from langchain_huggingface import HuggingFaceEmbeddings
from src.import_worker import ImportWorker
from src.category_workflow import CategoryWorkflow
from src.rag_embeddings_workflow import RagEmbeddingsWorkflow

logging.basicConfig(level=logging.INFO)
load_dotenv()
pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port="5432",
    database=os.getenv("DB_NAME"),
)
iw = ImportWorker(pool)
iw.run()
cw = CategoryWorkflow(pool=pool, pause_between_prompts=10)
cw.run()
hf_token = os.getenv("HF_TOKEN")
login(hf_token, add_to_git_credential=True)
os.environ["TOKENIZERS_PARALLELISM"] = "true"
shared_sentence_transformer = SentenceTransformer(
    "sentence-transformers/allenai-specter"
)
shared_hf_embeddings = HuggingFaceEmbeddings(model_name="allenai-specter")
rew = RagEmbeddingsWorkflow(
    pool=pool,
    sentence_transformer=shared_sentence_transformer,
    hf_embeddings=shared_hf_embeddings,
)
rew.erase_embeddings()
rew.run()
logging.info("ingest.py: Done!")
