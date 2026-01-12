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
from src.worker_mixin import WorkerMixin


class RagChat(AgentMixin, WorkerMixin):
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
        self.embeddings_agent = RagEmbeddingsWorkflow(
            pool=self.pool,
            sentence_transformer=sentence_transformer,
            hf_embeddings=hf_embeddings,
        )
        logging.basicConfig(level=logging.INFO)
        self.model = "gpt-5-mini"
        self.citations = []

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

    def retrieve_context_for_chat(self, text):
        """
        Retrieve chunks of context to send to LLM using the EmbeddingsAgent.

        Parameters
        ----------
        text : str
            Text to base the similarity search on.

        Returns
        -------
        List[Dict[str, str]]
            List of "agent" messages to send to LLM as context for the chat.
        """
        context = self.embeddings_agent.similiarity_search(text, k=15)
        context_messages = [
            {"role": "assistant", "content": f'Context {idx+1}: {piece["chunk"]}'}
            for idx, piece in enumerate(context)
        ]
        self.citations = list(set(piece["source"] for piece in context))
        return context_messages

    def prepare_and_send_history(self, history):
        system_content = self.prepare_prompt_from_file("openai_rag_system_prompt")
        messages = [{"role": "system", "content": system_content}]
        messages.extend(history)
        _, reply = self.call_openai_with_messages(messages, model=self.model)
        return {"role": "assistant", "content": reply}

    def log_message(self, message):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                sql = "INSERT INTO rag_prompts (prompt) VALUES (%s)"
                cur.execute(sql, (message,))
            conn.commit()

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
                            clear_button = gr.Button("Clear", variant="stop")
                    with gr.Row():
                        gr.Markdown("### Suggested prompts")
                    with gr.Row():
                        gr.Markdown(
                            "`What are challenges in metabolomics, as opposed to proteomics and genomics?`"
                        )
                    with gr.Row():
                        gr.Markdown(
                            "`What are problems encountered when matching lipidomics data to genome scale metabolic models in systems biology?`"
                        )
                    with gr.Row():
                        gr.Markdown(
                            "`What methods are available to integrate relatively quantified metabolite abundances with a genome scale metabolic model?`"
                        )
                with gr.TabItem("Embeddings"):
                    gr.Markdown("Coming soon!")

            def disable_clear_button():
                return gr.Button("Clear", variant="stop", interactive=False)

            def enable_clear_button():
                return gr.Button("Clear", variant="stop", interactive=True)

            def clear_chat():
                self.citations = []
                fresh_status = self.generate_status()
                return [], fresh_status

            def respond(message, chat_history):
                if len(chat_history) < 1:
                    self.log_message(message)
                    chat_history.extend(self.retrieve_context_for_chat(message))
                chat_history.append({"role": "user", "content": message})
                chat_history.append(self.prepare_and_send_history(chat_history))
                new_status_message = self.generate_status()
                return "", chat_history, new_status_message

            msg.submit(disable_clear_button, outputs=[clear_button]).then(
                respond, [msg, chatbot], [msg, chatbot, status_message]
            ).then(enable_clear_button, outputs=[clear_button])

            clear_button.click(clear_chat, outputs=[chatbot, status_message])

        return demo


if __name__ == "__main__":
    rc = RagChat()
    app = rc.gradio_app()
    app.launch(share=False)
