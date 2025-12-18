"""
FAISS Vector Store Implementation
Production-grade vector index for semantic search
"""

import numpy as np
import faiss
import pickle
from typing import List, Dict, Tuple
from pathlib import Path
from config import Config


class FAISSVectorStore:
    """FAISS-based vector store for efficient similarity search"""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = None
        self.metadata = []
        self.index_path = Path(Config.DATA_DIR) / 'faiss_index.bin'
        self.metadata_path = Path(Config.DATA_DIR) / 'faiss_metadata.pkl'
    
    def build_index(self, embeddings: np.ndarray, metadata: List[Dict]):
        """Build FAISS index from embeddings"""
        n_vectors = embeddings.shape[0]
        
        # Use IndexFlatIP for cosine similarity (after normalization)
        self.index = faiss.IndexFlatIP(self.dimension)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add vectors to index
        self.index.add(embeddings.astype('float32'))
        self.metadata = metadata
        
        print(f"Built FAISS index with {n_vectors} vectors")
    
    def save_index(self):
        """Persist index and metadata to disk"""
        Path(Config.DATA_DIR).mkdir(exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(self.index_path))
        
        # Save metadata
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
        
        print(f"Saved FAISS index to {self.index_path}")
    
    def load_index(self) -> bool:
        """Load index and metadata from disk"""
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))
            
            # Load metadata
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            
            print(f"Loaded FAISS index with {self.index.ntotal} vectors")
            return True
        except FileNotFoundError:
            print("FAISS index not found")
            return False
    
    def search(self, query_embedding: np.ndarray, top_k: int = 20) -> List[Tuple[Dict, float]]:
        """Search for most similar vectors"""
        # Normalize query
        query_norm = query_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_norm)
        
        # Search
        scores, indices = self.index.search(query_norm, top_k)
        
        # Return results with metadata
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.metadata):
                results.append((self.metadata[idx], float(score)))
        
        return results


if __name__ == "__main__":
    # Test FAISS vector store
    from embeddings import EmbeddingGenerator
    from data_processor import DataProcessor
    
    processor = DataProcessor()
    catalog = processor.load_catalog()
    
    if not catalog.empty:
        # Generate embeddings
        embedder = EmbeddingGenerator()
        embeddings = embedder.generate_catalog_embeddings(catalog)
        
        # Prepare metadata
        metadata = catalog.to_dict('records')
        
        # Build and save index
        store = FAISSVectorStore()
        store.build_index(embeddings, metadata)
        store.save_index()
        
        # Test search
        test_query = "Java developer with teamwork skills"
        query_emb = embedder.generate_query_embedding(test_query)
        results = store.search(query_emb, top_k=5)
        
        print(f"\nTop 5 results for: {test_query}\n")
        for meta, score in results:
            print(f"{meta['assessment_name']} ({meta['test_type']}) - Score: {score:.4f}")
