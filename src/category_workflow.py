import logging
from .agent_mixin import AgentMixin
from .worker_mixin import WorkerMixin


class CategoryWorkflow(AgentMixin, WorkerMixin):
    def __init__(self, pool, pause_between_prompts=20):
        """
        Instantiate the CategoryWorkflow

        Parameters
        ----------
        notififer : NotificationWorkflow
            A place to push notifications

        pool
            PostgreSQL connection pool.

        pause_between_prompts : int
            Number of seconds to pause between successive prompts to remain
            under API rate limits.
        """
        self.pool = pool
        self.pause_between_prompts = pause_between_prompts

    def select_uncategorized_uuids_and_titles(self):
        """
        Find papers that have not been categorized yet.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT uuid4, title FROM papers WHERE category IS NULL")
                results = cur.fetchall()
        return results

    def categorize_title(self, paper_title, max_category_len=100):
        """
        Categorize the given paper title with the Anthropic API.

        Parameters
        ----------
        paper_title : str
            Title to categorize

        max_category_len : int
            Maximum length of category allowed in database. If the LLM
            screws up and gives a long category, this truncates that
            category.

        Returns
        -------
        str
            The category of the paper based on its title as returned by
            the Anthropic API.
        """
        system_content = self.prepare_prompt_from_file(
            "claude_categorization_system_prompt"
        )
        user_content = self.prepare_prompt_from_file(
            "claude_categorization_user_prompt", {"paper_title": paper_title}
        )
        model, response = self.call_anthropic(
            system_content=system_content,
            user_content=user_content,
            pause_between_prompts=self.pause_between_prompts,
            notifier=self.notifier,
        )
        category = (
            response
            if len(response) < max_category_len
            else response[:max_category_len]
        )
        logging.info(
            f"CategoryAgent: {paper_title} categorized as {category} by {model}"
        )
        return category

    def update_category_for_uuid(self, paper_uuid4, category):
        """
        Updates the category for the paper UUID in PostgreSQL.

        Parameters
        ----------
        paper_uuid4 : str
            UUID of the paper the category is being set for.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE papers SET category = %s WHERE uuid4 = %s",
                    (category, paper_uuid4),
                )
            conn.commit()

    def run(self):
        """
        Find any uncategorized titles and categorize them with the Anthropic
        API. Send a push notification when all pending titles have been
        categorized.
        """
        unsummarized_uuids_and_titles = self.select_uncategorized_uuids_and_titles()
        logging.info(
            f"Found {len(unsummarized_uuids_and_titles)} papers to categorize."
        )
        for my_uuid4, title in unsummarized_uuids_and_titles:
            category = self.categorize_title(title)
            self.update_category_for_uuid(my_uuid4, category)
        n_categorized = len(unsummarized_uuids_and_titles)
        if n_categorized > 0:
            logging.info(f"CategoryWorkflow: Anthropic categorized {n_categorized} papers")
