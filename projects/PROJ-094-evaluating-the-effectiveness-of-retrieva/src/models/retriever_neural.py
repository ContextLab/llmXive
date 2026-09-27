"""
Neural Retriever using Sentence Transformers for dual-encoder code retrieval.

Implements T010: Dual-encoder retrieval using all-MiniLM-L6-v2.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from sentence_transformers import SentenceTransformer
from src.data.models import CodeSnippet, RetrievalMethod
from src.models.metrics import evaluate_metrics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NeuralRetriever:
    """
    Dual-encoder retriever using Sentence Transformers.
    
    Encodes queries and code snippets into a shared embedding space
    and retrieves the top-k most similar snippets via cosine similarity.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "cpu"):
        """
        Initialize the neural retriever.
        
        Args:
            model_name: Name of the sentence-transformers model to use.
            device: Device to run inference on ('cpu' or 'cuda').
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.snippet_embeddings: Optional[np.ndarray] = None
        self.snippets: List[CodeSnippet] = []
        self.index_loaded = False
        
        logger.info(f"Loading neural model: {model_name} on {device}")
        self.model = SentenceTransformer(model_name, device=device)
        logger.info("Model loaded successfully.")
    
    def build_index(self, snippets: List[CodeSnippet]) -> None:
        """
        Build the retrieval index by encoding all snippets.
        
        Args:
            snippets: List of CodeSnippet objects to index.
        """
        self.snippets = snippets
        texts = [s.code for s in snippets]
        
        logger.info(f"Encoding {len(texts)} snippets...")
        self.snippet_embeddings = self.model.encode(
            texts, 
            convert_to_numpy=True, 
            show_progress_bar=True,
            batch_size=32
        )
        
        # Normalize embeddings for cosine similarity
        norms = np.linalg.norm(self.snippet_embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        self.snippet_embeddings = self.snippet_embeddings / norms
        
        self.index_loaded = True
        logger.info(f"Index built successfully with {len(self.snippet_embeddings)} embeddings.")
    
    def retrieve(self, query: str, k: int = 10) -> List[Tuple[CodeSnippet, float]]:
        """
        Retrieve top-k snippets for a given query.
        
        Args:
            query: Natural language query string.
            k: Number of results to return.
        
        Returns:
            List of (CodeSnippet, score) tuples sorted by score descending.
        """
        if not self.index_loaded:
            raise RuntimeError("Index must be built before retrieval. Call build_index() first.")
        
        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True, show_progress_bar=False)
        query_norm = query_embedding / np.linalg.norm(query_norm) if (query_norm := np.linalg.norm(query_embedding)) > 0 else query_embedding
        
        # Compute cosine similarity
        scores = np.dot(self.snippet_embeddings, query_norm.T).flatten()
        
        # Get top-k indices
        top_k_indices = np.argsort(scores)[-k:][::-1]
        
        results = []
        for idx in top_k_indices:
            results.append((self.snippets[idx], float(scores[idx])))
        
        return results

def load_neural_retriever(
    model_path: Optional[str] = None,
    model_name: str = "all-MiniLM-L6-v2",
    device: str = "cpu"
) -> NeuralRetriever:
    """
    Load or create a NeuralRetriever instance.
    
    Args:
        model_path: Optional path to a saved model/index. If None, loads from HuggingFace.
        model_name: Name of the sentence-transformers model.
        device: Device for inference.
    
    Returns:
        Configured NeuralRetriever instance.
    """
    retriever = NeuralRetriever(model_name=model_name, device=device)
    
    if model_path and Path(model_path).exists():
        # Load pre-built index if available
        index_path = Path(model_path) / "index.pkl"
        if index_path.exists():
            import pickle
            with open(index_path, 'rb') as f:
                data = pickle.load(f)
                retriever.snippet_embeddings = data['embeddings']
                retriever.snippets = data['snippets']
                retriever.index_loaded = True
            logger.info(f"Loaded pre-built index from {model_path}")
        else:
            logger.warning(f"Index file not found at {index_path}, will build on first use.")
    
    return retriever

def evaluate_retrieval(
    retriever: NeuralRetriever,
    queries: List[Dict[str, Any]],
    k: int = 10
) -> Dict[str, Any]:
    """
    Evaluate the retriever against a set of ground-truth queries.
    
    Args:
        retriever: Trained NeuralRetriever instance.
        queries: List of query dicts with 'query', 'ground_truth_ids' keys.
        k: Cutoff for metrics.
    
    Returns:
        Dict containing per-query metrics and aggregate scores.
    """
    if not retriever.index_loaded:
        raise RuntimeError("Retriever index not built. Call build_index() first.")
    
    all_scores = []
    per_query_results = []
    
    for q in queries:
        query_text = q['query']
        ground_truth_ids = set(q.get('ground_truth_ids', []))
        
        if not ground_truth_ids:
            logger.warning(f"No ground truth for query: {query_text[:20]}... Skipping.")
            continue
        
        results = retriever.retrieve(query_text, k=k)
        
        retrieved_ids = [str(r[0].id) for r in results]
        
        # Compute metrics
        metrics = evaluate_metrics(retrieved_ids, ground_truth_ids, k=k)
        
        per_query_results.append({
            "query": query_text,
            "retrieved_ids": retrieved_ids,
            "metrics": metrics
        })
        
        all_scores.append(metrics['ndcg_at_k'])
    
    avg_ndcg = float(np.mean(all_scores)) if all_scores else 0.0
    
    return {
        "method": "neural",
        "model": retriever.model_name,
        "average_ndcg_at_k": avg_ndcg,
        "per_query_results": per_query_results
    }

def main():
    """
    Standalone script to demonstrate NeuralRetriever functionality.
    Loads processed data, builds index, and runs evaluation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Neural Retriever Evaluation")
    parser.add_argument("--data", type=str, default="data/processed/code_snippets.jsonl",
                        help="Path to processed JSONL data")
    parser.add_argument("--queries", type=str, default="data/processed/queries.jsonl",
                        help="Path to query JSONL file")
    parser.add_argument("--k", type=int, default=10, help="Cutoff for evaluation")
    parser.add_argument("--output", type=str, default="results/neural_retrieval_results.json",
                        help="Output JSON path")
    args = parser.parse_args()
    
    # Load processed snippets
    snippets = []
    if Path(args.data).exists():
        with open(args.data, 'r') as f:
            for line in f:
                data = json.loads(line)
                # Ensure ID is string for consistency
                data['id'] = str(data['id'])
                snippets.append(CodeSnippet(**{k: v for k, v in data.items() if k in CodeSnippet.__dataclass_fields__}))
        logger.info(f"Loaded {len(snippets)} snippets from {args.data}")
    else:
        logger.error(f"Data file not found: {args.data}")
        return
    
    # Load queries
    queries = []
    if Path(args.queries).exists():
        with open(args.queries, 'r') as f:
            for line in f:
                queries.append(json.loads(line))
        logger.info(f"Loaded {len(queries)} queries from {args.queries}")
    else:
        logger.error(f"Query file not found: {args.queries}")
        return
    
    # Initialize and build index
    retriever = load_neural_retriever()
    retriever.build_index(snippets)
    
    # Evaluate
    results = evaluate_retrieval(retriever, queries, k=args.k)
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Evaluation complete. Results saved to {output_path}")
    logger.info(f"Average nDCG@{args.k}: {results['average_ndcg_at_k']:.4f}")

if __name__ == "__main__":
    main()