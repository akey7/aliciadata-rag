import os
from contextlib import contextmanager


class WorkerMixin:
    """
    WorkerMixin provides common functionality for the workflows within
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
        print(type(self.db_pool))
        connection = self.db_pool.getconn()
        try:
            yield connection
        finally:
            self.db_pool.putconn(connection)

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
