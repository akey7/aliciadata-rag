import logging
import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
from src.import_worker import ImportWorker

logging.basicConfig(level=logging.INFO)
load_dotenv()
pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port="5432",
    database=os.getenv("DB_NAME"),
)
import_worker = ImportWorker(pool)
import_worker.run()
logging.info("ingest.py: Done!")
