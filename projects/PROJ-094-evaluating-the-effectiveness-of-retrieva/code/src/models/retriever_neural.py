"""
Neural Retriever using Sentence Transformers for dual-encoder retrieval.

Implements retrieval using sentence-transformers/all-MiniLM-L6-v2 model.
Supports batched inference for throughput optimization.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import psutil

from src.data.models import CodeSnippet, RetrievalMethod
from src.lib.utils import set_random_seed, setup_logging

logger = setup_logging(__name__)

# Default model configuration
DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MAX_BATCH_SIZE = 32
DEFAULT_TOP_K = 10

class NeuralRetriever:
    """
    Dual-encoder retrieval using Sentence Transformers.
    
    Encodes queries and code snippets into dense vectors and retrieves
    based on cosine similarity.
    """
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        device: str = "cpu",
        max_batch_size: int = MAX_BATCH_SIZE
    ):
        """
        Initialize the neural retriever.
        
        Args:
            model_name: Name of the sentence-transformers model to use
            device: Device to run inference on ("cpu" or "cuda")
            max_batch_size: Maximum batch size for inference
        """
        self.model_name = model_name
        self.device = device
        self.max_batch_size = max_batch_size
        self.model = None
        self.snippet_embeddings = None
        self.snippets = []
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the sentence-transformers model."""
        logger.info(f"Loading model: {self.model_name}")
        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(f"Model loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            raise
    
    def index_snippets(self, snippets: List[CodeSnippet]) -> None:
        """
        Encode and index a list of code snippets.
        
        Args:
            snippets: List of CodeSnippet objects to index
        """
        logger.info(f"Indexing {len(snippets)} snippets...")
        
        # Extract text content from snippets
        texts = [snippet.text for snippet in snippets]
        self.snippets = snippets
        
        # Generate embeddings in batches
        all_embeddings = []
        for i in range(0, len(texts), self.max_batch_size):
            batch_texts = texts[i:i + self.max_batch_size]
            batch_embeddings = self.model.encode(
                batch_texts,
                convert_to_numpy=True,
                show_progress_bar=(i == 0)  # Only show progress for first batch
            )
            all_embeddings.append(batch_embeddings)
            
            # Memory monitoring
            if i % (self.max_batch_size * 10) == 0:
                mem_usage = psutil.Process().memory_info().rss / 1024 / 1024
                logger.debug(f"Memory usage after {i} snippets: {mem_usage:.2f} MB")
        
        self.snippet_embeddings = np.vstack(all_embeddings)
        logger.info(f"Indexing complete. Shape: {self.snippet_embeddings.shape}")
    
    def retrieve(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K
    ) -> List[Tuple[CodeSnippet, float]]:
        """
        Retrieve top-k most similar snippets for a query.
        
        Args:
            query: The query string
            top_k: Number of results to return
            
        Returns:
            List of (CodeSnippet, score) tuples sorted by score descending
        """
        if self.snippet_embeddings is None:
            raise ValueError("No snippets indexed. Call index_snippets first.")
        
        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]
        
        # Compute similarities
        similarities = cosine_similarity([query_embedding], self.snippet_embeddings)[0]
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Return results
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            results.append((self.snippets[idx], score))
        
        return results
    
    def retrieve_batch(
        self,
        queries: List[str],
        top_k: int = DEFAULT_TOP_K
    ) -> List[List[Tuple[CodeSnippet, float]]]:
        """
        Retrieve results for multiple queries in batch.
        
        Args:
            queries: List of query strings
            top_k: Number of results per query
            
        Returns:
            List of result lists, one per query
        """
        if self.snippet_embeddings is None:
            raise ValueError("No snippets indexed. Call index_snippets first.")
        
        # Encode all queries in batches
        all_query_embeddings = []
        for i in range(0, len(queries), self.max_batch_size):
            batch_queries = queries[i:i + self.max_batch_size]
            batch_embeddings = self.model.encode(
                batch_queries,
                convert_to_numpy=True,
                show_progress_bar=(i == 0)
            )
            all_query_embeddings.append(batch_embeddings)
        
        query_embeddings = np.vstack(all_query_embeddings)
        
        # Compute similarities for all queries at once
        similarities = cosine_similarity(query_embeddings, self.snippet_embeddings)
        
        # Get top-k for each query
        results = []
        for i, sim_scores in enumerate(similarities):
            top_indices = np.argsort(sim_scores)[::-1][:top_k]
            query_results = []
            for idx in top_indices:
                score = float(sim_scores[idx])
                query_results.append((self.snippets[idx], score))
            results.append(query_results)
        
        return results
    
    def save_index(self, output_path: str) -> None:
        """
        Save the index to disk.
        
        Args:
            output_path: Path to save the index
        """
        if self.snippet_embeddings is None:
            raise ValueError("No index to save.")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save embeddings
        np.save(str(output_path / "embeddings.npy"), self.snippet_embeddings)
        
        # Save snippets metadata
        snippets_data = [
            {
                "id": s.id,
                "language": s.language,
                "text": s.text,
                "url": s.url,
                "docstring": s.docstring
            }
            for s in self.snippets
        ]
        with open(output_path / "snippets.json", "w", encoding="utf-8") as f:
            json.dump(snippets_data, f)
        
        # Save config
        config = {
            "model_name": self.model_name,
            "device": self.device,
            "num_snippets": len(self.snippets)
        }
        with open(output_path / "config.json", "w", encoding="utf-8") as f:
            json.dump(config, f)
        
        logger.info(f"Index saved to {output_path}")
    
    @classmethod
    def load_index(cls, index_path: str) -> "NeuralRetriever":
        """
        Load an index from disk.
        
        Args:
            index_path: Path to the saved index
            
        Returns:
            NeuralRetriever instance with loaded index
        """
        index_path = Path(index_path)
        
        # Load config
        with open(index_path / "config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # Create retriever
        retriever = cls(
            model_name=config["model_name"],
            device=config["device"]
        )
        
        # Load embeddings
        retriever.snippet_embeddings = np.load(index_path / "embeddings.npy")
        
        # Load snippets
        with open(index_path / "snippets.json", "r", encoding="utf-8") as f:
            snippets_data = json.load(f)
        
        retriever.snippets = [
            CodeSnippet(
                id=s["id"],
                language=s["language"],
                text=s["text"],
                url=s.get("url"),
                docstring=s.get("docstring")
            )
            for s in snippets_data
        ]
        
        logger.info(f"Index loaded from {index_path}")
        return retriever


def load_neural_retriever(
    snippets: List[CodeSnippet],
    model_name: str = DEFAULT_MODEL_NAME,
    device: str = "cpu"
) -> NeuralRetriever:
    """
    Convenience function to create and index a neural retriever.
    
    Args:
        snippets: List of CodeSnippet objects to index
        model_name: Model name to use
        device: Device to run on
        
    Returns:
        Initialized NeuralRetriever
    """
    retriever = NeuralRetriever(model_name=model_name, device=device)
    retriever.index_snippets(snippets)
    return retriever


def evaluate_retrieval(
    retriever: NeuralRetriever,
    queries: List[str],
    ground_truth: List[List[CodeSnippet]],
    top_k: int = DEFAULT_TOP_K
) -> Dict[str, Any]:
    """
    Evaluate retrieval performance against ground truth.
    
    Args:
        retriever: The neural retriever to evaluate
        queries: List of query strings
        ground_truth: List of ground truth snippet lists (one per query)
        top_k: Number of results to evaluate
        
    Returns:
        Dictionary with evaluation metrics
    """
    # Retrieve for all queries
    results = retriever.retrieve_batch(queries, top_k=top_k)
    
    # Calculate metrics
    hits = []
    recall_scores = []
    precision_scores = []
    
    for i, (query_results, gt) in enumerate(zip(results, ground_truth)):
        retrieved_ids = set(r[0].id for r in query_results)
        gt_ids = set(gt.id for gt in gt)
        
        # Hits@K
        hit = 1 if len(retrieved_ids & gt_ids) > 0 else 0
        hits.append(hit)
        
        # Recall@K
        if len(gt_ids) > 0:
            recall = len(retrieved_ids & gt_ids) / len(gt_ids)
        else:
            recall = 0.0
        recall_scores.append(recall)
        
        # Precision@K
        precision = len(retrieved_ids & gt_ids) / top_k
        precision_scores.append(precision)
    
    return {
        "method": RetrievalMethod.NEURAL.value,
        "hits_at_k": np.mean(hits),
        "recall_at_k": np.mean(recall_scores),
        "precision_at_k": np.mean(precision_scores),
        "num_queries": len(queries)
    }
