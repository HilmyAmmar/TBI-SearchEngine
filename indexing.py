import os
from elasticsearch import Elasticsearch
import csv
import logging
import time
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables and use your existing Elasticsearch client configuration
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use the same client configuration from your elasticsearch_client.py
es = Elasticsearch(
    os.getenv("ES_URL"),
    ca_certs=os.path.join(BASE_DIR, "TBI-SEARCHENGINE\certs", "http_ca.crt"),
    verify_certs=True,
    basic_auth=(
        os.getenv("ES_USERNAME"),
        os.getenv("ES_PASSWORD"),
    ),
    ssl_show_warn=False,
    ssl_assert_hostname=False,
)

# Define index name
index_name = "nfcorpus"

# Check if index exists and delete if necessary
if es.indices.exists(index=index_name):
    logger.info(f"Deleting existing index: {index_name}")
    es.indices.delete(index=index_name)

# Create index with mappings specifically for doc_dump.txt structure
index_settings = {
    "settings": {
        "analysis": {
            "analyzer": {
                "content_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop"]
                }
            }
        },
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "url": {"type": "keyword"},
            "title": {"type": "text", "analyzer": "content_analyzer"},
            "abstract": {"type": "text", "analyzer": "content_analyzer"}
        }
    }
}

# Create index
logger.info(f"Creating index: {index_name}")
es.indices.create(index=index_name, body=index_settings)

# Index documents from doc_dump.txt
def index_doc_dump():
    batch_size = 1000
    docs = []
    doc_count = 0
    
    start_time = time.time()
    logger.info(f"Starting indexing from doc_dump.txt")
    
    try:
        with open("nfcorpus/raw/doc_dump.txt", "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter='\t')
            
            for row in reader:
                if len(row) >= 4:
                    # Extract the 4 fields from doc_dump.txt
                    doc_id, url, title, abstract = row[0], row[1], row[2], row[3]
                    
                    # Prepare document with exactly these 4 fields
                    doc = {
                        "id": doc_id,
                        "url": url,
                        "title": title,
                        "abstract": abstract
                    }
                    
                    # Add to bulk operation
                    docs.append({"index": {"_index": index_name, "_id": doc_id}})
                    docs.append(doc)
                    doc_count += 1
                    
                    # Send batch to Elasticsearch
                    if len(docs) >= batch_size * 2:
                        es.bulk(body=docs)
                        logger.info(f"Indexed {doc_count} documents")
                        docs = []
            
            # Index any remaining documents
            if docs:
                es.bulk(body=docs)
                logger.info(f"Indexed final batch. Total documents: {doc_count}")
        
        # Refresh index to make documents searchable
        es.indices.refresh(index=index_name)
        elapsed_time = time.time() - start_time
        logger.info(f"Indexing completed. Total documents: {doc_count}, Time: {elapsed_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error during indexing: {str(e)}")
        raise

# Execute indexing
index_doc_dump()

# Test the index with a simple search
def test_search():
    count = es.count(index=index_name)
    logger.info(f"Document count in index: {count['count']}")
    
    # Simple search example
    test_query = {
        "query": {
            "match": {
                "title": "nutrition"
            }
        },
        "size": 5
    }
    
    results = es.search(index=index_name, body=test_query)
    hit_count = results['hits']['total']['value']
    logger.info(f"Search for 'nutrition' in title returned {hit_count} hits")
    
    # Show first result if available
    if hit_count > 0:
        first_hit = results['hits']['hits'][0]['_source']
        logger.info(f"Sample result - Title: {first_hit['title']}")
        logger.info(f"Sample result - Abstract: {first_hit['abstract'][:100]}...")

# Test the index
test_search()