import os

os.environ["TOKENIZERS_PARALLELISM"] = "true"
import logging
from dotenv import load_dotenv
import psycopg2
from psycopg2 import pool
import gradio as gr
from huggingface_hub import login
from sentence_transformers import SentenceTransformer
from langchain_huggingface import HuggingFaceEmbeddings
from src.rag_embeddings_workflow import RagEmbeddingsWorkflow


class RagChat:
    def __init__(self):
        load_dotenv()
        self.pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port="5432",
            database=os.getenv("DB_NAME"),
        )
        sentence_transformer = SentenceTransformer(
            "sentence-transformers/allenai-specter"
        )
        hf_embeddings = HuggingFaceEmbeddings(model_name="allenai-specter")
        self.rew = RagEmbeddingsWorkflow(
            pool=self.pool,
            sentence_transformer=sentence_transformer,
            hf_embeddings=hf_embeddings,
        )
        logging.basicConfig(level=logging.INFO)

    def gradio_app(self):
        with gr.Blocks(title="AliciaData RAG") as demo:
            gr.Markdown("# AliciaData RAG")
            with gr.Tabs():
                with gr.TabItem("Chat"):
                    gr.Markdown("Coming soon!")
                with gr.TabItem("Embeddings"):
                    gr.Markdown("Coming soon!")

        return demo


if __name__ == "__main__":
    rc = RagChat()
    app = rc.gradio_app()
    app.launch(share=False)
