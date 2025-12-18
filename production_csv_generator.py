"""
Production CSV Generator
Generates predictions for TEST SET ONLY
Strict format: Query,Assessment_url
"""

import pandas as pd
from pathlib import Path
from typing import List

from config import Config
from data_processor import DataProcessor
from vector_store import FAISSVectorStore
from embeddings import EmbeddingGenerator
from reranker import GenAIReranker


class ProductionCSVGenerator:
    """Generate competition submission CSV"""
    
    def __init__(self):
        self.processor = DataProcessor()
        self.embedder = EmbeddingGenerator()
        self.vector_store = FAISSVectorStore()
        self.reranker = GenAIReranker()
    
    def generate_test_predictions(self, output_file: str = None) -> pd.DataFrame:
        """
        Generate predictions for TEST SET
        
        CRITICAL: Do NOT use test set for training/tuning
        """
        if output_file is None:
            output_file = Config.OUTPUT_FILE
        
        print("\n" + "="*60)
        print("GENERATING TEST SET PREDICTIONS")
        print("="*60 + "\n")
        
        # Load catalog
        catalog_df = self.processor.load_catalog()
        if catalog_df.empty:
            raise ValueError("Catalog is empty")
        
        catalog_df = self.processor.normalize_data(catalog_df)
        
        # Load TEST set (unlabeled)
        test_df = self.processor.load_test_data()
        if test_df.empty:
            raise ValueError("Test data is empty")
        
        print(f"Loaded {len(test_df)} test queries")
        
        # Ensure vector store is ready
        if not self.vector_store.load_index():
            print("Building FAISS index...")
            embeddings = self.embedder.generate_catalog_embeddings(catalog_df)
            metadata = catalog_df.to_dict('records')
            self.vector_store.build_index(embeddings, metadata)
            self.vector_store.save_index()
        
        # Generate predictions
        results = []
        
        for idx, row in test_df.iterrows():
            query = row['query']
            
            print(f"Processing {idx+1}/{len(test_df)}: {query[:60]}...")
            
            # Get recommendations
            query_emb = self.embedder.generate_query_embedding(query)
            candidates_with_scores = self.vector_store.search(query_emb, top_k=20)
            
            # Convert to list
            candidates = []
            for meta, score in candidates_with_scores:
                meta['similarity_score'] = score
                candidates.append(meta)
            
            # Apply reranking
            recommendations = self.reranker.recommend(query, candidates, final_count=10)
            
            # Add to results (one row per recommendation)
            for rec in recommendations:
                results.append({
                    'Query': query,
                    'Assessment_url': rec['assessment_url']
                })
        
        # Create DataFrame
        output_df = pd.DataFrame(results)
        
        # Save to CSV
        Path(output_file).parent.mkdir(exist_ok=True)
        output_df.to_csv(output_file, index=False)
        
        print(f"\n{'='*60}")
        print(f"Predictions saved to: {output_file}")
        print(f"Total rows: {len(output_df)}")
        print(f"Unique queries: {output_df['Query'].nunique()}")
        print(f"{'='*60}\n")
        
        # Validation
        self._validate_output(output_df)
        
        return output_df
    
    def _validate_output(self, df: pd.DataFrame):
        """Validate CSV format"""
        required_cols = ['Query', 'Assessment_url']
        
        # Check columns
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns. Expected {required_cols}, got {df.columns.tolist()}")
        
        # Check for nulls
        if df['Query'].isna().any():
            raise ValueError("Found null values in Query column")
        
        if df['Assessment_url'].isna().any():
            raise ValueError("Found null values in Assessment_url column")
        
        # Check recommendations per query
        recs_per_query = df.groupby('Query').size()
        
        print("\nRecommendations per query:")
        for query, count in recs_per_query.items():
            if count < 5 or count > 10:
                print(f"  WARNING: {query[:50]}... has {count} recommendations (expected 5-10)")
            else:
                print(f"  ✓ {query[:50]}... : {count} recommendations")
        
        print("\n✓ CSV validation passed")


if __name__ == "__main__":
    generator = ProductionCSVGenerator()
    output_df = generator.generate_test_predictions()
