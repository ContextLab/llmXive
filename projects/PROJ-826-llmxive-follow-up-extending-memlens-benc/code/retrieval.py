"""
Retrieval module for MemLens using faiss-cpu for cosine similarity search.

Implements FR-003: Efficient retrieval of relevant memory snippets using
cosine similarity on pre-computed embeddings.
"""
import faiss
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import config

class RetrievalEngine:
    """
    Manages FAISS index construction and similarity search for memory retrieval.
    
    Uses cosine similarity by normalizing query and index vectors.
    Supports dynamic addition of embeddings and batch retrieval.
    """
    
    def __init__(self, dimension: int = 512):
        """
        Initialize the retrieval engine.
        
        Args:
            dimension: Dimension of the embedding vectors (default 512 for CLIP).
        """
        self.dimension = dimension
        self.index: Optional[faiss.IndexFlatIP] = None
        self.documents: List[Dict[str, Any]] = []
        self._is_normalized = False
        
    def build_index(self, embeddings: np.ndarray, documents: List[Dict[str, Any]]) -> None:
        """
        Build a FAISS index from pre-computed embeddings.
        
        For cosine similarity, we normalize vectors and use Inner Product (IP) index.
        
        Args:
            embeddings: Array of shape (n_samples, dimension) containing embeddings.
            documents: List of document metadata corresponding to each embedding.
        """
        if len(embeddings) == 0:
            raise ValueError("Cannot build index with empty embeddings.")
        
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension mismatch: expected {self.dimension}, got {embeddings.shape[1]}")
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self._is_normalized = True
        
        # Create FAISS index for inner product (cosine similarity after normalization)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings.astype('float32'))
        
        # Store documents for retrieval
        self.documents = documents
        
    def add_embeddings(self, embeddings: np.ndarray, documents: List[Dict[str, Any]]) -> None:
        """
        Add new embeddings to the existing index.
        
        Args:
            embeddings: Array of shape (n_samples, dimension).
            documents: List of document metadata corresponding to each embedding.
        """
        if self.index is None:
            self.build_index(embeddings, documents)
            return
        
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension mismatch: expected {self.dimension}, got {embeddings.shape[1]}")
        
        # Normalize new embeddings
        faiss.normalize_L2(embeddings)
        
        # Add to index
        self.index.add(embeddings.astype('float32'))
        
        # Append documents
        self.documents.extend(documents)
        
    def retrieve(
        self,
        query_embedding: np.ndarray,
        top_k: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], List[float]]:
        """
        Retrieve top-k most similar documents for a query embedding.
        
        Args:
            query_embedding: Query embedding vector of shape (dimension,) or (1, dimension).
            top_k: Number of results to return (defaults to config.TOP_K).
        
        Returns:
            Tuple of (documents, scores) where:
                - documents: List of retrieved document metadata
                - scores: List of cosine similarity scores
        """
        if self.index is None:
            raise RuntimeError("Index not built. Call build_index() first.")
        
        if top_k is None:
            top_k = config.TOP_K
        
        top_k = min(top_k, len(self.documents))
        
        # Ensure query is 2D
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Normalize query for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        # Perform search
        scores, indices = self.index.search(
            query_embedding.astype('float32'),
            top_k
        )
        
        # Extract results
        results = []
        score_list = []
        
        for i, idx in enumerate(indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            results.append(self.documents[idx])
            score_list.append(float(scores[0][i]))
        
        return results, score_list
    
    def retrieve_batch(
        self,
        query_embeddings: np.ndarray,
        top_k: Optional[int] = None
    ) -> Tuple[List[List[Dict[str, Any]]], List[List[float]]]:
        """
        Retrieve top-k documents for multiple query embeddings.
        
        Args:
            query_embeddings: Array of shape (n_queries, dimension).
            top_k: Number of results per query.
        
        Returns:
            Tuple of (all_results, all_scores) where each is a list of length n_queries.
        """
        if self.index is None:
            raise RuntimeError("Index not built. Call build_index() first.")
        
        if top_k is None:
            top_k = config.TOP_K
        
        top_k = min(top_k, len(self.documents))
        
        # Normalize all queries
        faiss.normalize_L2(query_embeddings)
        
        # Perform batch search
        scores, indices = self.index.search(
            query_embeddings.astype('float32'),
            top_k
        )
        
        all_results = []
        all_scores = []
        
        for i in range(len(query_embeddings)):
            results = []
            score_list = []
            for j, idx in enumerate(indices[i]):
                if idx == -1:
                    continue
                results.append(self.documents[idx])
                score_list.append(float(scores[i][j]))
            all_results.append(results)
            all_scores.append(score_list)
        
        return all_results, all_scores
    
    def get_index_size(self) -> int:
        """Return the number of vectors in the index."""
        return len(self.documents) if self.documents else 0
    
    def clear_index(self) -> None:
        """Clear the index and documents."""
        self.index = None
        self.documents = []
        self._is_normalized = False