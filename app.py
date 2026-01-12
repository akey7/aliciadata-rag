import gradio as gr


class RagChat:
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
