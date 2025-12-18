"""
FastAPI Production Server
Implements strict API schema and efficient request handling
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import uvicorn
from contextlib import asynccontextmanager
import logging

from api_models import (
    RecommendationRequest,
    RecommendationResponse,
    AssessmentResponse,
    HealthResponse
)
from config import Config
from data_processor import DataProcessor
from vector_store import FAISSVectorStore
from embeddings import EmbeddingGenerator
from reranker import GenAIReranker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
vector_store = None
embedder = None
reranker = None
catalog_df = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management - load models on startup"""
    global vector_store, embedder, reranker, catalog_df
    
    logger.info("Initializing SHL Recommendation System...")
    
    try:
        # Load components
        processor = DataProcessor()
        catalog_df = processor.load_catalog()
        
        if catalog_df.empty:
            raise RuntimeError("Catalog is empty")
        
        catalog_df = processor.normalize_data(catalog_df)
        
        # Initialize embedder
        embedder = EmbeddingGenerator()
        
        # Initialize FAISS vector store
        vector_store = FAISSVectorStore()
        
        if not vector_store.load_index():
            # Build index if not exists
            logger.info("Building FAISS index...")
            embeddings = embedder.generate_catalog_embeddings(catalog_df)
            metadata = catalog_df.to_dict('records')
            vector_store.build_index(embeddings, metadata)
            vector_store.save_index()
        
        # Initialize reranker
        reranker = GenAIReranker()
        
        logger.info("System initialized successfully")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        raise
    
    yield
    
    # Cleanup (if needed)
    logger.info("Shutting down...")


app = FastAPI(
    title="SHL Assessment Recommendation API",
    description="AI-powered assessment recommendation system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def map_test_type(test_type_code: str) -> List[str]:
    """Map K/P to full test type names"""
    mapping = {
        'K': ["Knowledge & Skills"],
        'P': ["Personality & Behavior"]
    }
    return mapping.get(test_type_code, ["Knowledge & Skills"])


def enrich_assessment(meta: dict) -> AssessmentResponse:
    """Enrich assessment with required fields"""
    return AssessmentResponse(
        name=meta['assessment_name'],
        url=meta['assessment_url'],
        adaptive_support="Yes",  # Default for SHL assessments
        description=meta['description'],
        duration=30,  # Default duration in minutes
        remote_support="Yes",  # SHL supports remote testing
        test_type=map_test_type(meta['test_type'])
    )


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "SHL Assessment Recommendation System",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "GET /health",
            "recommend": "POST /recommend"
        },
        "documentation": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if vector_store is None or vector_store.index is None:
        return HealthResponse(status="unhealthy", message="System not initialized")
    
    return HealthResponse(status="healthy", message="System operational")


@app.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest):
    """
    Main recommendation endpoint
    
    Returns 5-10 balanced assessments based on semantic similarity
    """
    try:
        # Validate system ready
        if vector_store is None or embedder is None:
            raise HTTPException(status_code=503, detail="System not ready")
        
        # Generate query embedding
        query_emb = embedder.generate_query_embedding(request.query)
        
        # Retrieve candidates using FAISS
        candidates_with_scores = vector_store.search(query_emb, top_k=request.top_k)
        
        # Convert to format expected by reranker
        candidates = []
        for meta, score in candidates_with_scores:
            meta['similarity_score'] = score
            candidates.append(meta)
        
        # Apply reranking and balancing
        recommendations = reranker.recommend(
            request.query,
            candidates,
            final_count=request.final_count
        )
        
        # Ensure 5-10 recommendations
        recommendations = recommendations[:max(5, min(10, request.final_count))]
        
        # Enrich and format response
        enriched = [enrich_assessment(rec) for rec in recommendations]
        
        return RecommendationResponse(recommended_assessments=enriched)
        
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global error handler"""
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=False,
        log_level="info"
    )
