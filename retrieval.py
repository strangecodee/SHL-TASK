import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
from config import Config
from embeddings import EmbeddingGenerator

class VectorRetrieval:
    def __init__(self):
        self.embedder = EmbeddingGenerator()
        self.catalog_df = None
        self.catalog_embeddings = None
    
    def load_catalog_and_embeddings(self, catalog_df: pd.DataFrame, embeddings: np.ndarray = None):
        self.catalog_df = catalog_df
        
        if embeddings is not None:
            self.catalog_embeddings = embeddings
        else:
            # Try to load embeddings from file
            self.catalog_embeddings = self.embedder.load_embeddings()
            
            # If still None, generate embeddings
            if self.catalog_embeddings is None:
                print("Generating embeddings as none were found...")
                self.catalog_embeddings = self.embedder.generate_catalog_embeddings(catalog_df)
                self.embedder.save_embeddings(self.catalog_embeddings)
        
        print(f"Retrieval engine ready with {len(self.catalog_df)} assessments")
    
    def retrieve_top_n(self, query: str, top_n: int = None) -> List[Dict]:
        if top_n is None:
            top_n = Config.TOP_N_RETRIEVAL
        
        # Generate query embedding
        query_embedding = self.embedder.generate_query_embedding(query)
        
        # Calculate similarity scores
        similarities = cosine_similarity(
            query_embedding.reshape(1, -1),
            self.catalog_embeddings
        )[0]
        
        # Sort indices by similarity (desc)
        sorted_indices = np.argsort(similarities)[::-1]
        
        results = []
        # Simple similarity floor to avoid totally irrelevant items
        min_sim = 0.20
        for idx in sorted_indices:
            score = float(similarities[idx])
            if score < min_sim:
                # Remaining items will be even less similar
                break
            result = {
                'assessment_name': self.catalog_df.iloc[idx]['assessment_name'],
                'assessment_url': self.catalog_df.iloc[idx]['assessment_url'],
                'test_type': self.catalog_df.iloc[idx]['test_type'],
                'description': self.catalog_df.iloc[idx]['description'],
                'category': self.catalog_df.iloc[idx]['category'],
                'similarity_score': score
            }
            results.append(result)
            if len(results) >= top_n:
                break
        
        return results
    
    def retrieve_with_filters(self, query: str, test_types: List[str] = None, 
                             categories: List[str] = None, top_n: int = None) -> List[Dict]:
        # First get top candidates
        candidates = self.retrieve_top_n(query, top_n=50)
        
        # Apply filters
        filtered_results = []
        for candidate in candidates:
            if test_types and candidate['test_type'] not in test_types:
                continue
            if categories and candidate['category'] not in categories:
                continue
            filtered_results.append(candidate)
        
        # Return top N after filtering
        if top_n is None:
            top_n = Config.TOP_N_RETRIEVAL
        
        return filtered_results[:top_n]

if __name__ == "__main__":
    from data_processor import DataProcessor
    
    # Load data
    processor = DataProcessor()
    catalog = processor.load_catalog()
    
    if catalog.empty:
        print("No catalog found. Please run scraper.py first.")
    else:
        # Initialize retrieval engine
        retriever = VectorRetrieval()
        retriever.load_catalog_and_embeddings(catalog)
        
        # Test retrieval
        test_query = "I am hiring for Java developers who can collaborate with business teams"
        results = retriever.retrieve_top_n(test_query, top_n=10)
        
        print(f"\nTop 10 results for: {test_query}\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['assessment_name']} ({result['test_type']})")
            print(f"   Score: {result['similarity_score']:.4f}")
            print(f"   URL: {result['assessment_url']}\n")
