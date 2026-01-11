import os
from contextlib import contextmanager


class WorkflowMixin:
    """
    WorkflowMixin provides common functionality for the workflows within
    knowledge-agent.
    """

    @contextmanager
    def get_connection(self):
        """
        Provides a context manager to manage the connection pool.
        Note: Any commits must be handled by the caller.

        Yields
        ------
        connection
            Yields connection from the pool.
        """
        connection = self.pool.getconn()
        try:
            yield connection
        finally:
            self.pool.putconn(connection)

    @property
    def db_connection_info(self):
        """
        Return dictionary of db connection info
        """
        return {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
        }

    def map_uuid_to_title(self, my_uuid4):
        """
        Map a UUID to a filename (within the knowledge agent folder structure)
        and and full-length title.

        Parameters
        ----------
        my_uuid4 : str
            The UUID of the paper, so named so that it does not shadow the uuid
            module.

        Returns
        -------
        str
            Full-length title of paper.

        Raises
        ------
        LookupError
            Raises a LookupError if the UUID is not found in the database.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT title FROM papers WHERE uuid4 = %s", (my_uuid4,))
                results = cur.fetchall()
        if not results:
            raise LookupError(f"WorkflowMixin: No title found for UUID {my_uuid4}")
        return results[0][0]

    def attribution(self, author_list, publication_year):
        """
        Creates an attribution in the form of:

        author(s), publication_year

        According to commonly used rules of authorship.

        Parameters
        ----------
        author_list : Listp[str]
            List of authors.

        publication_year : int
            The publication year.

        Returns
        -------
        str
            An attribution for the paper.
        """
        if len(author_list) == 1:
            return f"{author_list[0]} {publication_year}"
        elif len(author_list) == 2:
            return f"{author_list[0]} and {author_list[1]} {publication_year}"
        elif len(author_list) > 2:
            return f"{author_list[0]} et al {publication_year}"
        else:
            return "Unattributable"

    def map_uuid_to_metadata(self, paper_uuid4):
        """
        Map a paper UUID to its title and metdata. Return a dictionary with
        this information.

        Parameters
        ----------
        paper_uuid4 : str
            The UUID of the paper being retrieved.

        Returns
        -------
        Dict[str, Union[str, int, List[str]]]
            Dictionary with the following keys: "title", the title of the paper;
            "doi", the DOI of the paper; "author_list", List[str] of authors
            on the paper; "publication_year", year of publication; "attribution",
            attribution of the paper.

        Raises
        ------
        LookupError
            Raises a LookupError if the given uuid is not found.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT title, doi, author_list, publication_year, category FROM papers WHERE uuid4 = %s",
                    (paper_uuid4,),
                )
                results = cur.fetchall()
        if not results:
            raise LookupError(f"WorkflowMixin: No title found for UUID {paper_uuid4}")
        first_result = results[0]
        author_list = first_result[2].split(", ") if first_result[2] else "No authors"
        publication_year = int(first_result[3]) if first_result[3] else -1
        category = first_result[4]
        title_and_metadata = {
            "title": first_result[0],
            "doi": first_result[1],
            "author_list": author_list,
            "publication_year": publication_year,
            "category": category,
            "attribution": self.attribution(author_list, publication_year),
        }
        return title_and_metadata

    def read_file(self, filename):
        """
        Read a file into a string.

        Parameters
        ----------
        filename : str
            Filename to read.

        Returns
        -------
        str
            The contents of the file.
        """
        contents = ""
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                contents += line
        return contents

    def uuids_added_after_cutoff_interval(self, cutoff_interval="5 days"):
        """
        Query database for all UUIDs added after the provided cutoff interval
        (in SQL notation).

        Parameters
        ----------
        cutoff_interval : str
            Cutoff interval in SQL notation. Defaults to "5 days", which will
            retrieve all UUIDs added within the past 5 days.

        Returns
        -------
        Set[str]
            Set of UUIDs that match the criteria, if any.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT uuid4, title, datetime_added FROM papers WHERE datetime_added >= NOW() - INTERVAL %s",
                    (cutoff_interval,),
                )
                results = cur.fetchall()
        uuids = set(result[0] for result in results)
        return uuids

    def set_of_uuids_in_folder(self, folder_path, cutoff_interval=None):
        """
        Find the Set() of basenames (assumed to be UUIDs) contained
        in the specified folder. If an interval
        (such a "5 days") is specified, only those UUIDs at the intersection
        of what is in the folder and what was added since the cutoff are
        returned. If None (default), no restrictions are placed on the UUIDs
        returned.

        Parameters
        ----------
        folder_path : str
            Path to search for UUIDs in.

        cutoff_interval : str
            Cutoff interval in SQL notation. Defaults to None.

        Returns
        -------
        Set[str]
            Set of UUIDS in the folder and past the cutoff date (if specified)
        """
        basenames = []
        for _, _, files in os.walk(folder_path):
            for filename in files:
                if not filename.startswith("._") and "DS_Store" not in filename:
                    basenames.append(filename.replace(".md", "").replace(".json", ""))
        uuids_in_folder = set(basenames)
        if not cutoff_interval:
            return uuids_in_folder
        else:
            uuids_since_cutoff = self.uuids_added_after_cutoff_interval(cutoff_interval)
            return uuids_in_folder & uuids_since_cutoff
