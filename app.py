import os

os.environ["TOKENIZERS_PARALLELISM"] = "true"
import logging
from dotenv import load_dotenv
import psycopg2
from psycopg2 import pool
import gradio as gr
import pandas as pd
import plotly.graph_objects as go
from sklearn.manifold import TSNE
from huggingface_hub import login
from sentence_transformers import SentenceTransformer
from langchain_huggingface import HuggingFaceEmbeddings
from src.rag_embeddings_workflow import RagEmbeddingsWorkflow
from src.agent_mixin import AgentMixin
from src.worker_mixin import WorkerMixin


class RagChat(AgentMixin, WorkerMixin):
    def __init__(self):
        load_dotenv()
        self.db_pool = psycopg2.pool.SimpleConnectionPool(
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
            db_pool=self.db_pool,
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

    def embeddings_plot_data(self):
        """
        Prepare t-SNE plot data.

        Returns
        -------
        pd.DataFrame
            DataFrame suitable for plotting.
        """
        # embeddings_agent = RagEmbeddingsWorkflow(pool)
        embeddings, metadatas, paper_categories = (
            self.embeddings_agent.query_embeddings_and_metadatas()
        )
        tsne = TSNE(n_components=2, random_state=42)
        tsne_results = tsne.fit_transform(embeddings)
        clean_categories = [
            category.split("(")[0].strip() for category in paper_categories
        ]
        tooltips = [
            f'{metadata["paper_title"]} {metadata["chunk_index"]}'
            for metadata in metadatas
        ]
        df = pd.DataFrame(
            {
                "x": tsne_results[:, 0],
                "y": tsne_results[:, 1],
                "tooltip": tooltips,
                "category": clean_categories,
            }
        )
        return df

    def embeddings_plot(self):
        """
        Make a Plotly scatter plot of t-SNE data.
        """
        df = self.embeddings_plot_data()
        category_map = {
            "[Structural Biology & Protein Chemistry]": "black",
            "[Metabolic Pathways & Regulation]": "blue",
            "[Enzyme Mechanisms & Kinetics]": "red",
            "[Cell Signaling & Molecular Biology]": "orange",
            "[Disease Mechanisms & Therapeutic Targets]": "gray",
            "[Analytical Methods & Techniques]": "plum",
            "[Systems Biology & Computational Methods]": "tomato",
            "[Molecular Evolution & Comparative Biochemistry]": "turquoise",
            "[Bioenergetics & Membrane Biochemistry]": "limegreen",
            "[Chemical Biology & Synthetic Biology]": "magenta",
        }
        colors = [category_map[cat] for cat in df["category"]]
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df["x"],
                y=df["y"],
                mode="markers",
                marker=dict(size=10, color=colors),
                text=df["tooltip"],
                hoverinfo="text+x+y",
                showlegend=False,
            )
        )
        for category, color in category_map.items():
            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode="markers",
                    marker=dict(size=10, color=color),
                    name=category,
                )
            )
        fig.update_layout(
            title="Chunk Embeddings",
            xaxis=dict(title="t-SNE 1"),
            yaxis=dict(title="t-SNE 2"),
            template="plotly_white",
        )
        fig.update_layout(
            legend=dict(
                orientation="h",  # Horizontal orientation
                x=0.5,  # Center the legend horizontally
                y=-0.2,  # Move the legend below the plot
                xanchor="center",  # Align the center of the legend box
                yanchor="top",  # Align the top of the legend box
            ),
            height=1000,
        )
        return fig

    def chunk_citations_df(self):
        """
        Return a dataframe with all rows from the chunk_citations view.
        """
        df_rows = []
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT title, chunk_id, chunk_citation_count FROM chunk_citations"
                )
                results = cur.fetchall()
        for title, chunk_id, chunk_citation_count in results:
            df_rows.append(
                {
                    "Title": title,
                    "Chunk Id": chunk_id,
                    "Citation Count": chunk_citation_count,
                }
            )
        return pd.DataFrame(df_rows)

    def markdown_for_chunk_id(self, chunk_id):
        """
        Create a markdown with paper title and chunk contents for the given
        chunk_id. This markdown document is suitable to display on the UI.

        Parameters
        ----------
        chunk_id : np.int64
            The chunk id as a NumPy 64 bit integer. Will be case as a standard
            Python integer before being queried.

        Returns
        -------
        str
            Markdown document for display on the UI.
        """
        chunk_id_int = int(chunk_id)
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT p.title, cp.chunk FROM papers p INNER JOIN chunks_papers cp ON p.uuid4 = cp.paper_uuid4 WHERE cp.id = %s LIMIT 1",
                    (chunk_id_int,),
                )
                result = cur.fetchone()
                if not result:
                    raise LookupError(
                        f"markdown_for_chunk_id(): chunk_id {chunk_id} not found."
                    )
        paper_title, chunk = result
        return f'## From "{paper_title}"{os.linesep}{os.linesep}{chunk}{os.linesep}{os.linesep}--- End of chunk ---'

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
                    with gr.Row():
                        chunks_grdf = gr.DataFrame(
                            value=self.chunk_citations_df(),
                            wrap=False,
                            column_widths=[125, 15, 15],
                        )
                    with gr.Row():
                        with gr.Column():
                            chunk_display = gr.Markdown(
                                f"## Chunk text{os.linesep}{os.linesep}Select a chunk to see its contents"
                            )
                        with gr.Column():
                            gr.Plot(self.embeddings_plot())

            def on_chunk_select(evt: gr.SelectData):
                row = evt.index[0]
                chunk_id = self.chunk_citations_df().iloc[row, 1]
                logging.info(f"Selected Chunk Id: {chunk_id}")
                return self.markdown_for_chunk_id(chunk_id)

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
            chunks_grdf.select(on_chunk_select, inputs=None, outputs=[chunk_display])

        return demo


if __name__ == "__main__":
    rc = RagChat()
    app = rc.gradio_app()
    app.launch(share=False)
