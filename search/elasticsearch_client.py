import os
import tempfile
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_elasticsearch_client():
    """
    Create Elasticsearch client with proper certificate handling for Vercel deployment
    """
    ca_cert_content = os.getenv("HTTP_CA")
    
    if ca_cert_content:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.crt', delete=False) as cert_file:
            cert_file.write(ca_cert_content)
            cert_file_path = cert_file.name
        
        try:
            es = Elasticsearch(
                os.getenv("ES_URL"),
                ca_certs=cert_file_path,
                verify_certs=True,
                basic_auth=(
                    os.getenv("ES_USERNAME"),
                    os.getenv("ES_PASSWORD"),
                ),
                ssl_show_warn=False,
                ssl_assert_hostname=False,
            )
            
            es.ping()
            
        except Exception as e:
            print(f"Failed to connect with certificate: {e}")
            es = Elasticsearch(
                os.getenv("ES_URL"),
                verify_certs=False,
                basic_auth=(
                    os.getenv("ES_USERNAME"),
                    os.getenv("ES_PASSWORD"),
                ),
                ssl_show_warn=False,
            )
        finally:
            try:
                os.unlink(cert_file_path)
            except:
                pass
    else:
        print("No HTTP_CA certificate found, connecting without cert verification")
        es = Elasticsearch(
            os.getenv("ES_URL"),
            verify_certs=False,
            basic_auth=(
                os.getenv("ES_USERNAME"),
                os.getenv("ES_PASSWORD"),
            ),
            ssl_show_warn=False,
        )
    
    return es

es = get_elasticsearch_client()

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