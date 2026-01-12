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
from src.agent_mixin import AgentMixin


class RagChat(AgentMixin):
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
        self.citations = []
        self.model = "gpt-5-mini"

    def generate_status(self):
        """
        Generate a string of markdown that has citations for the RAG and
        the model being used.

        Returns
        -------
        str
            Markdown to render on the UI and save to the chat file.
        """
        if not self.citations:
            return f"""
# Model{os.linesep}{os.linesep}`{self.model}`
# Citations{os.linesep}{os.linesep}- Start the chat to see citations.
""".strip()
        else:
            citations_list = f"{os.linesep}1. ".join(self.citations)
            return f"""
# Model{os.linesep}{os.linesep}`{self.model}`
# Citations{os.linesep}{os.linesep}1. {citations_list}.
""".strip()

    def gradio_app(self):
        with gr.Blocks(title="AliciaData RAG") as demo:
            gr.Markdown("# AliciaData RAG")
            with gr.Tabs():
                with gr.TabItem("Chat"):
                    with gr.Row():
                        with gr.Column():
                            chatbot = gr.Chatbot()
                        with gr.Column():
                            status_message = gr.Markdown(self.generate_status())
                    with gr.Row():
                        with gr.Column():
                            msg = gr.Textbox(label="Prompt (press enter to send)")
                        with gr.Column():
                            clar_button = gr.Button("Clear", variant="stop")
                with gr.TabItem("Embeddings"):
                    gr.Markdown("Coming soon!")

        return demo


if __name__ == "__main__":
    rc = RagChat()
    app = rc.gradio_app()
    app.launch(share=False)
