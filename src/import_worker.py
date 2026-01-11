import logging
import os
import uuid
import hashlib
import shutil
import pandas as pd
from .workflow_mixin import WorkflowMixin
from .path_mixin import PathMixin


class ImportWorkflow(WorkflowMixin, PathMixin):
    def __init__(self, pool):
        """
        Instantiate a new ImportWorkflow.
        """
        self.pool = pool
        logging.info(
            f"ImportWorkflow: paper source {self.paper_source_folder}, paper storage {self.paper_storage_folder}"
        )

    def export_papers_table(self):
        """
        Export the papers table to a csv file that can be used to repopulate
        the most important table of the database if the database is corrupted.
        """
        df_rows = []
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT sha256, uuid4, title, category, datetime_added, doi, author_list, publication_year FROM papers"
                )
                results = cur.fetchall()
        for result in results:
            df_rows.append(
                {
                    "sha256": result[0],
                    "uuid4": result[1],
                    "title": result[2],
                    "category": result[3],
                    "datetime_added": result[4],
                    "doi": result[5],
                    "author_list": result[6],
                    "publication_year": result[7],
                }
            )
        datetime_stamp_underscore = self.datetime_stamp.replace(" ", "_")
        export_filename = os.path.join(
            self.papers_table_backups_folder, f"papers{datetime_stamp_underscore}.csv"
        )
        pd.DataFrame(df_rows).to_csv(export_filename, index=False, quoting=1)

    def read_uuid4_and_title_for_sha256(self, sha256):
        """
        Read the UUID and title corresponding to a SHA256.

        Parameters
        ----------
        sha256 : str
            The SHA256 digest to query.

        Returns
        -------
        List[Tuple]
            The rows returned by the database query. If this list is empty,
            the SHA256 was not found.
        """
        with self.get_connection() as connection:
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT uuid4, title FROM papers WHERE sha256 = %s", (sha256,)
                )
                results = cur.fetchall()

        return results

    def insert_sha256_uuid4_and_title_into_papers(self, sha256, my_uuid4, title):
        """
        Insert a new SHA256, UUID, and title into the papers table.

        Paremeters
        ----------
        sha256 : str
            The string of the hex digest of the SHA256 signature.

        my_uuid4 : str
            The UUID4 to insert.

        title : str
            The full-length title of the paper.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO papers (uuid4, title, sha256) VALUES (%s, %s, %s)",
                    (my_uuid4, title, sha256),
                )
            conn.commit()

    def calculate_file_sha256(self, full_path):
        """
        Calculate the SHA256 of a file.

        Parameters
        ----------
        full_path : str
            Absolute path to the file.

        Returns
        -------
        str
            SHA256 hex digest of the file.
        """
        sha256_hash = hashlib.sha256()
        with open(full_path, "rb") as file:
            chunk = file.read(8192)
            while chunk:
                sha256_hash.update(chunk)
                chunk = file.read(8192)
        return sha256_hash.hexdigest()

    def dump_md_for_uuid(self, my_uuid4):
        """
        Print the text of the paper referenced by the given UUID to stdout.

        Parameters
        ----------
        my_uuid4 : str
            The UUID of the paper to print.
        """
        title = self.map_uuid_to_title(my_uuid4)
        filename = os.path.join(self.paper_storage_folder, f"{my_uuid4}.md")
        print("# ABSOLUTE PATH")
        print(filename)
        print("# TITLE")
        print(title)
        print("# TEXT")
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                print(line.strip())

    def run(self):
        """
        Look for new papers in the import folder and bring them into the
        knowledge agent system if they have not already been imported.
        (Papers are considered imported if their SHA256 is already in
        the database).
        """
        count = 0
        for root, _, files in os.walk(self.paper_source_folder):
            for filename in files:
                if (
                    filename.endswith(".txt")
                    or filename.endswith(".md")
                    and not filename.startswith("._")
                ):
                    full_path = os.path.join(root, filename)
                    sha256 = self.calculate_file_sha256(full_path)
                    rows = self.read_uuid4_and_title_for_sha256(sha256)
                    if not rows:
                        my_uuid4 = str(uuid.uuid4())
                        title = filename.replace(".txt", "").replace(".md", "")
                        destination_path = os.path.join(
                            self.paper_storage_folder, f"{my_uuid4}.md"
                        )
                        shutil.copy2(full_path, destination_path)
                        self.insert_sha256_uuid4_and_title_into_papers(
                            sha256, my_uuid4, title
                        )
                        logging.info(f"ImportWorkflow: Added title {title}")
                        count += 1
        if count > 0:
            self.export_papers_table()
            logging.info(f"ImportWorkflow: Imported {count} papers")
