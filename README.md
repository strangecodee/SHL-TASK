# SHL Assessment Recommendation System

Production-grade AI-powered recommendation system for SHL assessments using FAISS vector search and semantic embeddings.

## Quick Start

```powershell
# Install dependencies
pip install -r requirements.txt

# One-command execution (builds index, evaluates, generates CSV, starts API)
python run.py
```

## System Architecture

```
Query → Embedding (all-MiniLM-L6-v2) → FAISS Search → Reranking → 5-10 Balanced Recommendations
```

## Key Features

- **FAISS Vector Search**: Efficient semantic search over 54 SHL assessments
- **Sentence Transformers**: all-MiniLM-L6-v2 embeddings (384-dim)
- **K/P Balancing**: Automatic balancing between Knowledge & Skills / Personality & Behavior
- **FastAPI Server**: Production-ready async API with Pydantic validation
- **Recall@10 Evaluation**: Mean Recall@10: 0.48 on train set

## Tech Stack

- Python 3.11
- FastAPI + Uvicorn
- FAISS-CPU (IndexFlatIP for cosine similarity)
- sentence-transformers
- Pydantic 2.x
- pandas + openpyxl

## Project Structure

```
SHL-TASK/
├── api_server.py              # FastAPI production server
├── api_models.py              # Pydantic schemas
├── vector_store.py            # FAISS index management
├── embeddings.py              # Sentence transformer embeddings
├── reranker.py                # K/P balancing logic
├── production_evaluator.py    # Recall@10 evaluation
├── production_csv_generator.py # Test predictions
├── data_processor.py          # Excel data loading
├── config.py                  # Configuration
├── run.py                     # Main execution script
├── requirements.txt           # Dependencies
├── Gen_AI Dataset.xlsx        # Train/Test data
└── data/
    ├── shl_catalog.csv        # 54 assessments
    ├── faiss_index.bin        # FAISS index
    ├── faiss_metadata.pkl     # Assessment metadata
    ├── recommendations_output.csv # Submission file
    └── evaluation_results.json    # Metrics
```

## API Endpoints

### GET /
```json
{
  "service": "SHL Assessment Recommendation System",
  "version": "1.0.0",
  "status": "operational",
  "endpoints": {
    "health": "GET /health",
    "recommend": "POST /recommend"
  },
  "documentation": "/docs"
}
```

### GET /health
```json
{"status": "healthy", "message": "System operational"}
```

### POST /recommend

**Request:**
```json
{
  "query": "Java developers with teamwork skills",
  "top_k": 20,
  "final_count": 10
}
```

**Response:**
```json
{
  "recommended_assessments": [
    {
      "name": "Core Java Advanced Level New",
      "url": "https://www.shl.com/solutions/products/product-catalog/view/core-java-advanced-level-new/",
      "adaptive_support": "Yes",
      "description": "Core Java Advanced Level New assessment for comprehensive evaluation",
      "duration": 30,
      "remote_support": "Yes",
      "test_type": ["Knowledge & Skills"]
    }
  ]
}
```

## Manual Execution

```powershell
# 1. Build catalog from training data (already done)
# Creates data/shl_catalog.csv with 54 assessments

# 2. Build FAISS index
python vector_store.py

# 3. Evaluate on train set (65 queries)
python production_evaluator.py
# Output: Mean Recall@10: 0.48

# 4. Generate test predictions (9 queries, 90 rows)
python production_csv_generator.py
# Output: data/recommendations_output.csv

# 5. Start API server
python api_server.py
# Server: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## Performance Metrics

- **Catalog Size**: 54 assessments (42 K-type, 12 P-type)
- **Train Set**: 65 queries
- **Test Set**: 9 queries
- **Mean Recall@10**: 0.48 (baseline), 0.46 (with reranking)
- **Embedding Dimension**: 384
- **Top-K Retrieval**: 20 candidates
- **Final Output**: 10 recommendations per query

## Output Files

### recommendations_output.csv
Submission file with 90 rows (9 queries × 10 recommendations)
```csv
Query,Assessment_url
"Looking to hire...","https://www.shl.com/..."
```

### evaluation_results.json
```json
{
  "baseline": {"mean_recall_at_10": 0.48},
  "pipeline": {"mean_recall_at_10": 0.46}
}
```

## Configuration

Edit [config.py](file:///d:/linux/P1/AI/SHL-TASK/config.py):

```python
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
TOP_N_RETRIEVAL = 20
FINAL_RECOMMENDATIONS = 10
API_HOST = '0.0.0.0'
API_PORT = 8000
```

## Dependencies

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sentence-transformers==2.2.2
faiss-cpu==1.7.4
pandas==2.1.3
openpyxl==3.1.5
numpy==1.24.3
```

## Testing

```powershell
# Test API endpoints
python test_production_api.py
```

## Notes

- Catalog built from Train-Set URLs (54 unique assessments)
- All URLs match training data format
- System uses rule-based K/P balancing (no Gemini API required)
- FAISS index uses IndexFlatIP for exact cosine similarity
- API serves from pre-built index (no real-time embedding generation overhead)
