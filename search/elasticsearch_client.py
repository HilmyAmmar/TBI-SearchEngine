import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

es = Elasticsearch(
    os.getenv("ES_URL"),
    ca_certs=os.getenv("HTTP_CA"),
    verify_certs=True,
    basic_auth=(
        os.getenv("ES_USERNAME"),
        os.getenv("ES_PASSWORD"),
    ),
    ssl_show_warn=False,
    ssl_assert_hostname=False,
)

def create_index(index_name):
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body={
            "mappings": {
                "properties": {
                    "url": {"type": "keyword"},
                    "title": {"type": "text"},
                    "abstract": {"type": "text"}
                }
            }
        })