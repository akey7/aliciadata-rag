import gradio as gr

def create_app():
    with gr.Blocks(title="AliciaData RAG") as demo:
        gr.Markdown("# AliciaData RAG")
        with gr.Tabs():
            with gr.TabItem("Chat"):
                gr.Markdown("Coming soon!")
            with gr.TabItem("Embeddings"):
                gr.Markdown("Coming soon!")

    return demo

if __name__ == "__main__":
    app = create_app()
    app.launch(share=False)
