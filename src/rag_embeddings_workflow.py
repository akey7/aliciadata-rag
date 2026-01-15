"""
Enables storage and retrieval of chunks and embeddings for RAG.
"""


import logging
import os
import chromadb
from langchain_community.document_loaders import BSHTMLLoader
from langchain_text_splitters import MarkdownTextSplitter
from sentence_transformers import SentenceTransformer
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from .worker_mixin import WorkerMixin
from .path_mixin import PathMixin


class RagEmbeddingsWorkflow(WorkerMixin, PathMixin):
    def __init__(
        self,
        db_pool,
        sentence_transformer=None,
        hf_embeddings=None,
        suggested_chunk_size_characters=3000,
        overlap_size_characters=300,
        min_chunk_size_characters=600,
    ):
        """
        Instantiate a new EmbeddingsWorkflow to handle document embeddings.

        Parameters
        ----------
        db_pool
            PostgreSQL connection pool.

        sentence_trasnsformer : SentenceTransformer, optional
            SentenceTransformer to encode embeddings for insertions
            into Chroma. If left as default of none, a new SentenceTransformer
            will be instantiated.

        hf_embeddings : HuggingFaceEmbeddings
            HuggingFacEmbeddings to use with Chroma searches. If left as default
            of none, a new HuggingFacEmbeddings will be instantiated.

        suggested_chunk_size_characters : int
            The desired and approximate size of each chunk to be extracted.

        overlap_size_characters : int
            The overlap size across chunks.

        min_chunk_size_characters : int
            The minimum chunk length allowed to be placed in the vector store.
        """
        self.chroma_client = chromadb.HttpClient(host="localhost", port=8000)
        self.chroma_collection = self.chroma_client.get_or_create_collection("default")
        self.suggested_chunk_size_characters = suggested_chunk_size_characters
        self.overlap_size_characters = overlap_size_characters
        self.min_chunk_size_characters = min_chunk_size_characters
        self.db_pool = db_pool
        self.sentence_transformer = (
            sentence_transformer
            if sentence_transformer
            else SentenceTransformer("sentence-transformers/allenai-specter")
        )
        self.hf_embeddings = (
            hf_embeddings
            if hf_embeddings
            else HuggingFaceEmbeddings(model_name="allenai-specter")
        )
        logging.info(
            f"RagEmbeddingsWorkflow: suggested_chunk_size_characters={suggested_chunk_size_characters}, overlap_size_characters={overlap_size_characters}, min_chunk_size_characters={min_chunk_size_characters}"
        )

    def find_unembedded_papers(self):
        """
        Finds UUIDs of the papers that have been imported by ImportAgent
        but have not been put into the vector database.

        Returns
        -------
        List[str]
            List of UUIDs of unembedded papers.
        """
        unembedded_uuids_sql = """
        SELECT t1.uuid4 
        FROM papers t1
        LEFT JOIN chunks_papers t2 ON t1.uuid4 = t2.paper_uuid4 
        WHERE t2.paper_uuid4 IS NULL
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(unembedded_uuids_sql)
                results = cur.fetchall()

        return [result[0] for result in results]

    def insert_chunks_from_paper(self, paper_uuid4, sentence_transformer):
        """
        Take the paper referenced by the given UUID, split it into chunks,
        calculates the embedding vector, and inserts the chunks into the
        chunks_papers table and vector store.

        Parameters
        ----------
        paper_uuid4 : str
            UUID of the paper being chunked.

        sentence_transformer : SentenceTransformer
            The sentence transformer to be used for the embeddings.
        """
        paper_title = self.map_uuid_to_title(paper_uuid4)
        filename = os.path.join(self.paper_storage_folder, f"{paper_uuid4}.md")
        loader = BSHTMLLoader(filename)  # Strips out html tags!
        document = loader.load()
        text_splitter = MarkdownTextSplitter(
            chunk_size=self.suggested_chunk_size_characters,
            chunk_overlap=self.overlap_size_characters,
            length_function=len,
        )
        chunks = text_splitter.split_documents(document)
        for chunk in chunks:
            self.insert_uuid4_and_chunk_into_chunks_papers(
                paper_uuid4, chunk.page_content
            )
        chunk_ids = []
        chunk_contents = []
        chunk_metadatas = []
        for chunk_index, chunk in enumerate(chunks):
            if len(chunk.page_content) >= self.min_chunk_size_characters:
                chunk_ids.append(f"{paper_uuid4}_{chunk_index}")
                chunk_contents.append(chunk.page_content)
                chunk_metadatas.append(
                    {
                        "paper_title": paper_title,
                        "chunk_index": chunk_index,
                        "paper_uuid4": paper_uuid4,
                    }
                )
        vectors = sentence_transformer.encode(chunk_contents)
        self.chroma_collection.add(
            ids=chunk_ids,
            documents=chunk_contents,
            metadatas=chunk_metadatas,
            embeddings=vectors,
        )
        logging.info(
            f'Inserted {len(chunks)} chunks from {paper_uuid4} "{paper_title}" into chunks_papers and vector store.'
        )

    def insert_uuid4_and_chunk_into_chunks_papers(self, paper_uuid4, chunk):
        """
        Insert a new record of a chunk of text in the chunks_papers table.

        Parameters
        ----------
        paper_uuid4 : str
            The UUID of the paper.

        chunk : str
            The contents of the chunk as a string.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chunks_papers (paper_uuid4, chunk) VALUES (%s, %s)",
                    (paper_uuid4, chunk),
                )
            conn.commit()

    def erase_embeddings(self):
        """
        Erases all the vector embeddings. Useful if all the embeddings need to
        be changed to a different model, or something like that. A drastic
        measure that is not part of routine operation.
        """
        ids = self.chroma_collection.get()["ids"]
        self.chroma_collection.delete(ids=ids)
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chunk_retrievals")
                cur.execute("DELETE FROM chunks_papers")
            conn.commit()
        logging.info("RagEmbeddingsWorkflow: All embeddings have been erased.")

    def sources_for_chunks(self, chunks):
        """
        Return a list of titles from which the given chunks were drawn from
        the vector store.

        Parameters
        ----------
        chunks : List[str]
            A list of chunks to lookup.

        Returns
        -------
        List[str]
            List of titles corresponding to the chunks.

        Raises
        ------
        LookupError
            Raises a LookupError if a chunk is not found.
        """
        titles = []
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for chunk in chunks:
                    cur.execute(
                        "SELECT DISTINCT title FROM papers p INNER JOIN chunks_papers cp ON p.uuid4 = cp.paper_uuid4 WHERE cp.chunk = %s LIMIT 1",
                        (chunk,),
                    )
                    results = cur.fetchall()
                    titles.append(results[0][0])
        if not titles:
            raise LookupError(f"RagEmbeddingsWorkflow: Chunk not found.")
        return titles

    def similiarity_search(self, text, k=5):
        """
        Run a similarity search based on the given text and return k similar
        chunks of text.

        Parameters
        ----------
        text : str
            Text for the simularity search, perhaps from a prompt you need
            context for.

        k : int
            Number of chunks to return

        Returns
        -------
        List[str]
            Returns a list of chunks from the search.
        """
        vectorstore = Chroma(
            client=self.chroma_client,
            embedding_function=self.hf_embeddings,
            collection_name="default",
        )
        docs_found = vectorstore.search(text, search_type="similarity", k=k)
        chunks = [doc.page_content for doc in docs_found]
        sources = self.sources_for_chunks(chunks)
        self.insert_chunk_retrievals(chunks)
        result = [
            {"chunk": chunk, "source": source} for chunk, source in zip(chunks, sources)
        ]
        logging.info(f"EmbeddingsAgent: Retrieved {len(result)} documents.")
        return result

    def insert_chunk_retrievals(self, chunks):
        """
        Insert chunks retrieved by the vector db into the chunk_retrievals table.
        This enables tracking how many times chunks are retrieved as a way to
        surface the most important chunks.

        Parameters
        ----------
        chunks: List[str]
            List of strings, with each string being the contents of a chunk.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for chunk in chunks:
                    cur.execute(
                        "INSERT INTO chunk_retrievals (chunk_id) VALUES ((SELECT id FROM chunks_papers WHERE chunk = %s LIMIT 1))",
                        (chunk,),
                    )
            conn.commit()

    def query_embeddings_and_metadatas(self):
        """
        Return all embeddings, metadata, and paper categories as lists.

        Returns
        -------
        List[np.array], List[Dict], List[str]
             embeddings, metadatas, paper_categories in that order.
        """
        embeddings_metadatas = self.chroma_collection.get(
            include=["embeddings", "metadatas"]
        )
        embeddings = embeddings_metadatas["embeddings"]
        metadatas = embeddings_metadatas["metadatas"]
        paper_categories = []
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for metadata in metadatas:
                    paper_uuid4 = metadata["paper_uuid4"]
                    cur.execute(
                        "SELECT category FROM papers WHERE uuid4 = %s LIMIT 1",
                        (paper_uuid4,),
                    )
                    result = cur.fetchone()
                    paper_categories.append(result[0])
        return embeddings, metadatas, paper_categories

    def run(self):
        """
        Calls appropriate functions to fid unembedded papers and add them
        to the vector store.
        """
        unembedded_uuid4s = self.find_unembedded_papers()
        logging.info(f"Found {len(unembedded_uuid4s)} unembedded papers.")
        if len(unembedded_uuid4s) > 0:
            for my_uuid4 in unembedded_uuid4s:
                self.insert_chunks_from_paper(my_uuid4, self.sentence_transformer)
