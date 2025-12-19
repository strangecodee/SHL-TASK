# SHL Assessment Recommendation System - Submission Files

## Core Implementation Files

1. `api_server.py` - FastAPI production server
2. `api_models.py` - Pydantic schemas for request/response validation
3. `vector_store.py` - FAISS index management
4. `embeddings.py` - Sentence transformer embeddings
5. `reranker.py` - K/P balancing logic and Gemini API integration
6. `production_evaluator.py` - Recall@10 evaluation
7. `production_csv_generator.py` - Test predictions generator
8. `data_processor.py` - Excel data loading and processing
9. `config.py` - Configuration management
10. `run.py` - Main execution script

## Data Files

1. `Gen_AI Dataset.xlsx` - Original dataset with Train-Set and Test-Set sheets
2. `data/shl_catalog.csv` - Processed catalog of 54 SHL assessments
3. `data/faiss_index.bin` - FAISS vector index binary
4. `data/faiss_metadata.pkl` - Assessment metadata for FAISS index
5. `data/train_queries.csv` - Training queries extracted from dataset
6. `data/test_queries.csv` - Test queries extracted from dataset

## Output Files

1. `data/anurag_maurya.csv` - Final submission file with 2762 rows
2. `data/evaluation_results.json` - Detailed evaluation metrics

## Supporting Files

1. `requirements.txt` - Python dependencies
2. `Dockerfile` - Containerization configuration
3. `docker-compose.yml` - Multi-container deployment
4. `README.md` - System documentation
5. `DEPLOYMENT.md` - Detailed deployment instructions
6. `.env.example` - Environment variable template
7. `.gitignore` - Version control exclusions
8. `SHL_Assessment_Recommendation_Report.md` - This comprehensive report

## Files Excluded from Submission

1. `.env` - Contains sensitive API keys (use `.env.example` as template)
2. Cache directories (`__pycache__`, `.qoder`, `.venv`, `.venv311`) - Temporary files
3. Any `.pyc`, `.pyo`, `.pyd` files - Compiled Python files

## Instructions for Running the System

1. Install dependencies: `pip install -r requirements.txt`
2. (Optional) Add Gemini API key to `.env` file based on `.env.example`
3. Run the complete pipeline: `python run.py`

The system will:
- Build FAISS index from the catalog
- Evaluate performance on training data
- Generate recommendations for test queries
- Start the API server on http://localhost:8001