import os
import re
from datetime import datetime


class PathMixin:
    """
    PathMixin provides the paths to the many folders and files of the
    knowledge-agent system. Each method computes the requisite location,
    checks if it exists, and returns it if it does exist.
    """

    @property
    def knowledge_agent_data_folder(self):
        knowledge_agent_data_dir = os.getenv("KNOWLEDGE_AGENT_DATA_FOLDER")
        if not os.path.exists(knowledge_agent_data_dir):
            raise FileNotFoundError(
                f"PathMixin: knowledge_agent_data_folder {knowledge_agent_data_dir} not found."
            )
        return knowledge_agent_data_dir

    @property
    def knowledge_agent_audio_folder(self):
        knowledge_agent_audio_dir = os.getenv("KNOWLEDGE_AGENT_AUDIO_FOLDER")
        if not os.path.exists(knowledge_agent_audio_dir):
            raise FileNotFoundError(
                f"PathMixin: knowledge_agent_audio_folder {knowledge_agent_audio_dir} not found."
            )
        return knowledge_agent_audio_dir

    @property
    def paper_source_folder(self):
        paper_source_dir = os.getenv("PAPER_SOURCE_FOLDER")
        if not os.path.exists(paper_source_dir):
            raise FileNotFoundError(
                f"PathMixin: paper_source_folder {paper_source_dir} does not exist."
            )
        return paper_source_dir

    @property
    def paper_storage_folder(self):
        paper_storage_dir = os.path.join(self.knowledge_agent_data_folder, "md_storage")
        if not os.path.exists(paper_storage_dir):
            raise FileNotFoundError(
                f"PathMixin: paper_storage_folder {paper_storage_dir} does not exist."
            )
        return paper_storage_dir

    @property
    def obsidian_export_folder(self):
        obsidian_export_dir = os.getenv("OBSIDIAN_EXPORT_FOLDER")
        if not os.path.exists(obsidian_export_dir):
            raise FileNotFoundError(
                f"PathMixin: obsidian_export_folder {obsidian_export_dir} not found."
            )
        return obsidian_export_dir

    @property
    def openai_summaries_folder(self):
        openai_summaries_dir = os.path.join(
            self.knowledge_agent_data_folder, "summaries", "OpenAI"
        )
        if not os.path.exists(openai_summaries_dir):
            raise FileNotFoundError(
                f"PathMixin: OpenAI summaries folder {openai_summaries_dir} does not exist"
            )
        return openai_summaries_dir

    @property
    def anthropic_summaries_folder(self):
        anthropic_summaries_dir = os.path.join(
            self.knowledge_agent_data_folder, "summaries", "Anthropic"
        )
        if not os.path.exists(anthropic_summaries_dir):
            raise FileNotFoundError(
                f"PathMixin: Anthropic summaries folder {anthropic_summaries_dir} does not exist"
            )
        return anthropic_summaries_dir

    @property
    def gemini_summaries_folder(self):
        gemini_summaries_dir = os.path.join(
            self.knowledge_agent_data_folder, "summaries", "Gemini"
        )
        if not os.path.exists(gemini_summaries_dir):
            raise FileNotFoundError(
                f"PathMixin: Gemini summaries folder {gemini_summaries_dir} does not exit."
            )
        return gemini_summaries_dir

    @property
    def discussions_folder(self):
        discussions_dir = os.path.join(self.knowledge_agent_data_folder, "discussions")
        if not os.path.exists(discussions_dir):
            raise FileNotFoundError(
                f"PathMixin: Discussion folder {discussions_dir} not found"
            )
        return discussions_dir

    @property
    def selected_logs_folder(self):
        selected_logs_dir = os.path.join(self.obsidian_export_folder, "Selected Logs")
        if not os.path.exists(selected_logs_dir):
            raise FileNotFoundError(
                f"PathMixin: Selected logs folder {selected_logs_dir} not found"
            )
        return selected_logs_dir

    @property
    def rag_chats_folder(self):
        rag_chats_dir = os.path.join(self.obsidian_export_folder, "RAG Chats")
        if not os.path.exists(rag_chats_dir):
            raise FileNotFoundError(
                f"PathMixin: Rag chats folder {rag_chats_dir} not found"
            )
        return rag_chats_dir

    @property
    def insight_retrievals_folder(self):
        insight_retrievals_dir = os.path.join(
            self.obsidian_export_folder, "Insight Retrievals"
        )
        if not os.path.exists(insight_retrievals_dir):
            raise FileNotFoundError(
                f"PathMixin: Insight retrievals folder {insight_retrievals_dir} not found"
            )
        return insight_retrievals_dir

    @property
    def datetime_stamp(self):
        return datetime.now().strftime("%Y-%m-%d %H%M%S")

    @property
    def openai_digests_folder(self):
        openai_digests_dir = os.path.join(
            self.knowledge_agent_data_folder, "digests", "OpenAI"
        )
        if not os.path.exists(openai_digests_dir):
            raise FileNotFoundError(
                f"PathMixin: OpenAI digests folder {openai_digests_dir} not fuond"
            )
        return openai_digests_dir

    @property
    def papers_table_backups_folder(self):
        papers_table_backups_dir = os.path.join(
            self.knowledge_agent_data_folder, "papers_table_backups"
        )
        if not os.path.exists(papers_table_backups_dir):
            raise FileNotFoundError(
                f"PathMixin: Could not find paper table backups folder {papers_table_backups_dir}"
            )
        return papers_table_backups_dir

    @property
    def literature_reviews_folder(self):
        literature_reviews_dir = os.path.join(
            self.obsidian_export_folder, "Literature Reviews"
        )
        if not os.path.exists(literature_reviews_dir):
            raise FileNotFoundError(
                f"PathMixin: Could not find literature review folder {literature_reviews_dir}"
            )
        return literature_reviews_dir

    def truncate_and_clean_title(self, title):
        """
        Shorten a given title to be 60 characters or less, which is a
        covenient length for filenames in an Obsidian vault.

        Parameters
        ----------
        title : str
            Full-length title to truncate

        Returns
        -------
        str
            Truncated title.
        """
        short_title = title if len(title) < 61 else title[:61]
        pattern = re.compile(r"[^a-zA-Z0-9\-\. ]+|\s+")
        clean_title = pattern.sub(
            lambda m: " " if " " in m.group() else "", short_title
        ).strip()
        return clean_title
