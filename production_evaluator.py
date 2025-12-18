"""
Production Evaluation Module
Implements strict Recall@10 metric on TRAIN SET ONLY
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from pathlib import Path
import json

from config import Config
from data_processor import DataProcessor
from vector_store import FAISSVectorStore
from embeddings import EmbeddingGenerator
from reranker import GenAIReranker


class ProductionEvaluator:
    """Strict evaluation following competition guidelines"""
    
    def __init__(self):
        self.processor = DataProcessor()
        self.embedder = EmbeddingGenerator()
        self.vector_store = FAISSVectorStore()
        self.reranker = GenAIReranker()
        self.results = []
    
    def parse_relevant_urls(self, url_string: str) -> List[str]:
        """Parse semicolon-separated URLs"""
        if pd.isna(url_string) or not url_string:
            return []
        return [url.strip() for url in str(url_string).split(';') if url.strip()]
    
    def calculate_recall_at_k(self, predicted: List[str], relevant: List[str], k: int = 10) -> float:
        """
        Recall@K = (# relevant in top-K) / (# total relevant)
        
        CRITICAL: Exact implementation as per assignment
        """
        if not relevant:
            return 0.0
        
        predicted_top_k = predicted[:k]
        relevant_found = sum(1 for url in relevant if url in predicted_top_k)
        
        return relevant_found / len(relevant)
    
    def evaluate_train_set(self, use_reranking: bool = True) -> Dict:
        """
        Evaluate on TRAIN SET ONLY
        
        Args:
            use_reranking: If True, use full pipeline; else baseline retrieval only
        """
        print(f"\n{'='*60}")
        print(f"Evaluating: {'Full Pipeline' if use_reranking else 'Baseline Retrieval'}")
        print(f"{'='*60}\n")
        
        # Load catalog
        catalog_df = self.processor.load_catalog()
        if catalog_df.empty:
            raise ValueError("Catalog is empty")
        
        catalog_df = self.processor.normalize_data(catalog_df)
        
        # Load TRAIN set
        train_df = self.processor.load_train_data()
        if train_df.empty:
            raise ValueError("Train data is empty")
        
        # Ensure vector store is ready
        if not self.vector_store.load_index():
            print("Building FAISS index...")
            embeddings = self.embedder.generate_catalog_embeddings(catalog_df)
            metadata = catalog_df.to_dict('records')
            self.vector_store.build_index(embeddings, metadata)
            self.vector_store.save_index()
        
        # Evaluate each query
        recalls = []
        query_results = []
        
        for idx, row in train_df.iterrows():
            query = row['query']
            relevant_urls = self.parse_relevant_urls(row.get('relevant_urls', ''))
            
            if not relevant_urls:
                print(f"Query {idx+1}: No relevant URLs, skipping")
                continue
            
            # Get predictions
            query_emb = self.embedder.generate_query_embedding(query)
            candidates_with_scores = self.vector_store.search(query_emb, top_k=20)
            
            # Convert to list of dicts
            candidates = [meta for meta, score in candidates_with_scores]
            for i, (meta, score) in enumerate(candidates_with_scores):
                candidates[i]['similarity_score'] = score
            
            if use_reranking:
                # Apply reranking + balancing
                recommendations = self.reranker.recommend(query, candidates, final_count=10)
            else:
                # Baseline: top 10 by similarity
                recommendations = candidates[:10]
            
            predicted_urls = [r['assessment_url'] for r in recommendations]
            
            # Calculate Recall@10
            recall = self.calculate_recall_at_k(predicted_urls, relevant_urls, k=10)
            recalls.append(recall)
            
            query_results.append({
                'query': query,
                'recall_at_10': recall,
                'relevant_count': len(relevant_urls),
                'predicted_urls': predicted_urls[:5]  # Store top 5 for review
            })
            
            print(f"Query {idx+1}/{len(train_df)}: Recall@10 = {recall:.4f}")
        
        # Calculate metrics
        mean_recall = np.mean(recalls) if recalls else 0.0
        
        result = {
            'method': 'Full Pipeline' if use_reranking else 'Baseline',
            'mean_recall_at_10': mean_recall,
            'num_queries': len(recalls),
            'query_details': query_results
        }
        
        print(f"\n{'='*60}")
        print(f"Mean Recall@10: {mean_recall:.4f}")
        print(f"Queries evaluated: {len(recalls)}")
        print(f"{'='*60}\n")
        
        return result
    
    def run_full_evaluation(self) -> pd.DataFrame:
        """Run both baseline and full pipeline evaluation"""
        
        # Baseline
        baseline_results = self.evaluate_train_set(use_reranking=False)
        
        # Full pipeline
        pipeline_results = self.evaluate_train_set(use_reranking=True)
        
        # Calculate improvement
        improvement = pipeline_results['mean_recall_at_10'] - baseline_results['mean_recall_at_10']
        
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)
        print(f"Baseline Mean Recall@10:  {baseline_results['mean_recall_at_10']:.4f}")
        print(f"Pipeline Mean Recall@10:  {pipeline_results['mean_recall_at_10']:.4f}")
        print(f"Improvement:              {improvement:.4f}")
        
        if baseline_results['mean_recall_at_10'] > 0:
            pct = (improvement / baseline_results['mean_recall_at_10']) * 100
            print(f"Relative Improvement:     {pct:.2f}%")
        
        print("="*60 + "\n")
        
        # Save detailed results
        output_path = Path(Config.DATA_DIR) / 'evaluation_results.json'
        with open(output_path, 'w') as f:
            json.dump({
                'baseline': baseline_results,
                'pipeline': pipeline_results,
                'improvement': improvement
            }, f, indent=2)
        
        print(f"Detailed results saved to {output_path}")
        
        # Return summary DataFrame
        summary_df = pd.DataFrame([
            {
                'Method': 'Baseline',
                'Mean_Recall@10': baseline_results['mean_recall_at_10'],
                'Queries': baseline_results['num_queries']
            },
            {
                'Method': 'Full Pipeline',
                'Mean_Recall@10': pipeline_results['mean_recall_at_10'],
                'Queries': pipeline_results['num_queries']
            }
        ])
        
        return summary_df


if __name__ == "__main__":
    evaluator = ProductionEvaluator()
    results_df = evaluator.run_full_evaluation()
    print("\n", results_df)
