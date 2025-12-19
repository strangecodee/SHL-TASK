# Configuration settings for SHL Assessment Recommendation System

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # SHL Catalog Configuration
    SHL_CATALOG_URL = 'https://www.shl.com/solutions/products/product-catalog/'
    
    # Model Configuration
    EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
    TOP_N_RETRIEVAL = 20
    FINAL_RECOMMENDATIONS = 10
    
    # Balancing Strategy
    TECHNICAL_K_RATIO = 0.7
    TECHNICAL_P_RATIO = 0.3
    BEHAVIORAL_K_RATIO = 0.3
    BEHAVIORAL_P_RATIO = 0.7
    MIXED_K_RATIO = 0.5
    MIXED_P_RATIO = 0.5
    
    # File Paths
    DATA_DIR = 'data'
    CATALOG_FILE = os.path.join(DATA_DIR, 'shl_catalog.csv')
    EMBEDDINGS_FILE = os.path.join(DATA_DIR, 'catalog_embeddings.npy')
    TRAIN_DATA_FILE = os.path.join(DATA_DIR, 'train_queries.csv')
    TEST_DATA_FILE = os.path.join(DATA_DIR, 'test_queries.csv')
    OUTPUT_FILE = os.path.join(DATA_DIR, 'anurag_maurya.csv')
    
    # Excel dataset (Gen_AI Dataset.xlsx)
    GEN_AI_DATASET_FILE = 'Gen_AI Dataset.xlsx'
    TRAIN_SHEET_NAME = 'Train-Set'
    TEST_SHEET_NAME = 'Test-Set'
    
    # API Configuration
    API_HOST = '0.0.0.0'
    API_PORT = 8000
    API_TIMEOUT = 30
