# TBI-SearchEngine: Medical RAG Search Engine 🔍🏥

A Django-based **Retrieval-Augmented Generation (RAG)** search engine for medical and nutrition information. This system combines Elasticsearch for document retrieval with Mistral AI for intelligent answer generation.

## 🌟 Features

- **🎯 Intelligent Query Expansion**: Automatically expands medical queries with relevant terms
- **📚 Document Retrieval**: Fast search through medical corpus using Elasticsearch
- **🤖 AI-Powered Answers**: Generates comprehensive answers using Mistral AI
- **🔧 Configurable Results**: Customizable top-k document retrieval
- **📊 Rich Response Format**: Returns both search results and AI-generated answers
- **⚡ Health Monitoring**: Built-in health checks for Elasticsearch and LLM services

## 🏗️ Architecture

```
User Query → Query Expansion (Mistral AI) → Elasticsearch Search → RAG Generation (Mistral AI) → Response
```

**Tech Stack:**
- **Backend**: Django REST Framework
- **Search Engine**: Elasticsearch
- **LLM**: Mistral AI (via HuggingFace Hub)
- **Data**: NFCorpus medical/nutrition dataset

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Elasticsearch 7.x/8.x
- HuggingFace API key

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd TBI-SearchEngine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
# Elasticsearch Configuration
ES_URL=https://your-elasticsearch-url:9200
ES_USERNAME=elastic
ES_PASSWORD=your-elasticsearch-password

# Mistral AI Configuration (via HuggingFace)
API_KEY=your-huggingface-api-key

# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key
```

### 3. Data Indexing

**Download NFCorpus Dataset:**
```bash
# Create directory and download data
mkdir -p nfcorpus/raw
# Download nfdump.txt to nfcorpus/raw/nfdump.txt
```

**Index the data into Elasticsearch:**
```bash
python indexing_nfdump.py
```

### 4. Run the Server

```bash
# Apply Django migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

## 📡 API Endpoints

### 1. **Search with RAG**
```http
GET /search/?q=<query>&k=<number>
```

**Parameters:**
- `q` (required): Search query
- `k` (optional): Number of documents to retrieve (default: 5, max: 20)

**Example:**
```bash
curl "http://localhost:8000/search/?q=what%20causes%20diabetes&k=5"
```

**Response:**
```json
{
  "query": {
    "original": "what causes diabetes",
    "expanded_terms": ["Type 1 diabetes etiology", "insulin resistance"],
    "final_search_query": "what causes diabetes Type 1 diabetes etiology..."
  },
  "search_results": {
    "total_found": 1269,
    "returned_count": 5,
    "k_requested": 5,
    "documents": [...]
  },
  "rag_answer": {
    "answer": "Diabetes is primarily caused by...",
    "confidence": "high"
  }
}
```

### 2. **Health Checks**

**Elasticsearch Health:**
```http
GET /health/elasticsearch/
```

**LLM Health:**
```http
GET /health/llm/
```

## 🔧 Configuration

### Elasticsearch Settings
- **Index**: `medicine`
- **Fields**: `title`, `abstract`, `main_text`, `url`
- **Analyzer**: Custom content analyzer with lowercase and stop word filters

### LLM Settings
- **Model**: `mistralai/Mistral-7B-Instruct-v0.3`
- **Query Expansion**: 3-5 relevant medical terms
- **Answer Generation**: Max 600 tokens, temperature 0.2

## 📁 Project Structure

```
TBI-SearchEngine/
├── search/                     # Main Django app
│   ├── views.py               # RAG logic and API endpoints
│   ├── elasticsearch_client.py # ES connection setup
│   ├── mistral_client.py      # Mistral AI client
│   ├── urls.py               # URL routing
│   └── models.py             # Django models
├── searchengine/             # Django project settings
├── indexing_nfdump.py        # Data indexing script
├── requirements.txt          # Python dependencies
├── manage.py                # Django management script
└── .env                     # Environment variables
```

## 🎯 Usage Examples

### Basic Medical Query
```python
import requests

response = requests.get(
    "http://localhost:8000/search/",
    params={"q": "symptoms of diabetes", "k": 3}
)
data = response.json()

print("Answer:", data["rag_answer"]["answer"])
print("Sources:", len(data["search_results"]["documents"]))
```

### Nutrition Research
```python
response = requests.get(
    "http://localhost:8000/search/",
    params={"q": "benefits of plant based diet", "k": 10}
)
```

## ⚡ Performance Optimization

**Current Performance:**
- Query expansion: ~3-8 seconds
- Document retrieval: ~0.1-0.5 seconds
- Answer generation: ~5-20 seconds
- **Total**: ~8-28 seconds

**Optimization Tips:**
1. **Reduce LLM token limits** for faster responses
2. **Enable caching** for repeated queries
3. **Use async processing** for parallel operations
4. **Lower temperature** settings for deterministic results

## 🔍 Monitoring

Check system health:
```bash
# Elasticsearch status
curl http://localhost:8000/health/elasticsearch/

# LLM service status  
curl http://localhost:8000/health/llm/
```

## 📊 Data Schema

**Document Fields:**
- `id`: Unique identifier
- `title`: Document title
- `main_text`: Full document content
- `abstract`: Document summary
- `url`: Source URL
- `topics_tags`: Related medical topics
- `description`: Brief description

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🆘 Troubleshooting

### Common Issues:

**Elasticsearch Connection Error:**
```bash
# Check ES status
curl -k https://your-elasticsearch-url:9200/_cluster/health

# Verify credentials in .env file
```

**LLM API Error:**
```bash
# Verify HuggingFace API key
# Check rate limits and quotas
```

**Slow Response Times:**
- Reduce `max_tokens` in LLM calls
- Enable query caching
- Use smaller batch sizes for indexing

## 📚 Related Resources

- [Elasticsearch Documentation](https://www.elastic.co/guide/)
- [Mistral AI Models](https://huggingface.co/mistralai)
- [NFCorpus Dataset](https://www.cl.uni-heidelberg.de/statnlpgroup/nfcorpus/)
- [Django REST Framework](https://www.django-rest-framework.org/)

---

**Built with ❤️ for medical information retrieval and AI-powered question answering.** 
