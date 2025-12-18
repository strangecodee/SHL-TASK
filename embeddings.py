import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from typing import List
from config import Config
import os

class EmbeddingGenerator:
    def __init__(self, model_name: str = None):
        if model_name is None:
            model_name = Config.EMBEDDING_MODEL
        
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.catalog_embeddings = None
        self.catalog_df = None
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        print(f"Generating embeddings for {len(texts)} texts...")
        embeddings = self.model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        return embeddings
    
    def generate_catalog_embeddings(self, catalog_df: pd.DataFrame) -> np.ndarray:
        self.catalog_df = catalog_df
        
        # Use combined_text if available, otherwise create it
        if 'combined_text' not in catalog_df.columns:
            texts = catalog_df.apply(
                lambda row: f"{row['assessment_name']} {row['category']} {row['description']}", 
                axis=1
            ).tolist()
        else:
            texts = catalog_df['combined_text'].tolist()
        
        self.catalog_embeddings = self.generate_embeddings(texts)
        print(f"Generated embeddings shape: {self.catalog_embeddings.shape}")
        
        return self.catalog_embeddings
    
    def save_embeddings(self, embeddings: np.ndarray, filepath: str = None):
        if filepath is None:
            filepath = Config.EMBEDDINGS_FILE
        
        np.save(filepath, embeddings)
        print(f"Embeddings saved to {filepath}")
    
    def load_embeddings(self, filepath: str = None) -> np.ndarray:
        if filepath is None:
            filepath = Config.EMBEDDINGS_FILE
        
        try:
            self.catalog_embeddings = np.load(filepath)
            print(f"Loaded embeddings from {filepath}, shape: {self.catalog_embeddings.shape}")
            return self.catalog_embeddings
        except FileNotFoundError:
            print(f"Embeddings file not found at {filepath}")
            return None
    
    def generate_query_embedding(self, query: str) -> np.ndarray:
        return self.model.encode([query], convert_to_numpy=True)[0]

if __name__ == "__main__":
    from data_processor import DataProcessor
    
    # Load catalog
    processor = DataProcessor()
    catalog = processor.load_catalog()
    
    if catalog.empty:
        print("No catalog found. Please run scraper.py first.")
    else:
        # Generate and save embeddings
        embedder = EmbeddingGenerator()
        embeddings = embedder.generate_catalog_embeddings(catalog)
        embedder.save_embeddings(embeddings)
