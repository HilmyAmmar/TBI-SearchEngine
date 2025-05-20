import os
from elasticsearch import Elasticsearch
import csv
import logging
import time
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use the Elasticsearch client with increased timeout settings
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
    request_timeout=120,  # Increase the request timeout to 2 minutes
    max_retries=5,        # Increase retry attempts
    retry_on_timeout=True  # Retry on timeout
)

# Define index name
index_name = "medicine"

# Check if index exists and delete if necessary
if es.indices.exists(index=index_name):
    logger.info(f"Deleting existing index: {index_name}")
    es.indices.delete(index=index_name)

# Create index with mappings for nfdump.txt fields
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
        "number_of_replicas": 0,
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "url": {"type": "keyword"},
            "title": {"type": "text", "analyzer": "content_analyzer"},
            "main_text": {"type": "text", "analyzer": "content_analyzer"},
            "comments": {"type": "text", "analyzer": "content_analyzer"},
            "topics_tags": {"type": "keyword"},
            "description": {"type": "text", "analyzer": "content_analyzer"},
            "doctors_note": {"type": "text", "analyzer": "content_analyzer"},
            "article_links": {"type": "keyword"},
            "question_links": {"type": "keyword"},
            "topic_links": {"type": "keyword"},
            "video_links": {"type": "keyword"},
            "medarticle_links": {"type": "keyword"}
        }
    }
}

# Create index
logger.info(f"Creating index: {index_name}")
es.indices.create(index=index_name, body=index_settings)

# Index documents from nfdump.txt
def index_nfdump():
    # Much smaller batch size
    batch_size = 25  # Reduce dramatically from 500
    docs = []
    doc_count = 0
    error_count = 0

    start_time = time.time()
    logger.info(f"Starting indexing from nfdump.txt")

    try:
        # Increase the field size limit
        csv.field_size_limit(10000000)  # 10MB

        with open("nfcorpus/raw/nfdump.txt", "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter='\t')

            for row in reader:
                try:
                    # Ensure we have at least the ID field
                    if len(row) >= 1:
                        # Create document with available fields
                        doc = {
                            "id": row[0]
                        }

                        # Add remaining fields if available
                        field_names = ["url", "title", "main_text", "comments", "topics_tags",
                                       "description", "doctors_note", "article_links", "question_links",
                                       "topic_links", "video_links", "medarticle_links"]

                        for i, field_name in enumerate(field_names, 1):
                            if i < len(row):
                                # For link fields, only add if non-empty
                                if field_name.endswith('_links') and row[i]:
                                    links = [link.strip() for link in row[i].split(
                                        ',') if link.strip()]
                                    if links:
                                        doc[field_name] = links
                                # Process topics tags to array
                                elif field_name == 'topics_tags' and row[i]:
                                    tags = [tag.strip() for tag in row[i].split(
                                        ',') if tag.strip()]
                                    if tags:
                                        doc[field_name] = tags
                                # Normal text fields - only add if they have content
                                elif row[i]:
                                    doc[field_name] = row[i]

                        # Add to bulk operation
                        docs.append(
                            {"index": {"_index": index_name, "_id": doc["id"]}})
                        docs.append(doc)
                        doc_count += 1

                        # Send batch to Elasticsearch - much smaller batches
                        if len(docs) >= batch_size * 2:
                            try:
                                es.bulk(body=docs, timeout="2m")
                                logger.info(f"Indexed {doc_count} documents")
                            except Exception as bulk_err:
                                error_count += 1
                                logger.error(
                                    f"Error in bulk indexing batch: {str(bulk_err)}")
                                if error_count > 5:
                                    logger.error("Too many errors, aborting")
                                    raise
                            docs = []
                except Exception as row_err:
                    logger.warning(f"Error processing row: {str(row_err)}")
                    continue

            # Index any remaining documents
            if docs:
                try:
                    es.bulk(body=docs, timeout="2m")
                    logger.info(
                        f"Indexed final batch. Total documents: {doc_count}")
                except Exception as e:
                    logger.error(f"Error in final bulk indexing: {str(e)}")

        # Refresh index to make documents searchable
        es.indices.refresh(index=index_name)
        elapsed_time = time.time() - start_time
        logger.info(
            f"Indexing completed. Total documents: {doc_count}, Time: {elapsed_time:.2f} seconds")

    except Exception as e:
        logger.error(f"Error during indexing: {str(e)}")
        raise

# Execute indexing
index_nfdump()

# Test the index with a simple search
def test_search():
    try:
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
        logger.info(f"Search for 'nutrition' returned {hit_count} hits")

        # Show first result if available
        if hit_count > 0:
            first_hit = results['hits']['hits'][0]['_source']
            logger.info(
                f"Sample result - Title: {first_hit.get('title', 'N/A')}")
    except Exception as e:
        logger.error(f"Error testing search: {str(e)}")

# Test the index
test_search()
