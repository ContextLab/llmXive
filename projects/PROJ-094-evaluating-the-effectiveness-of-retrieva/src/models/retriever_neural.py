"""
Neural Retriever using Sentence Transformers for dual-encoder retrieval.

Implements dense vector retrieval using pre-trained sentence embeddings.
Uses `sentence-transformers/all-MiniLM-L6-v2` as the default model.

This module provides:
- NeuralRetriever class for indexing and retrieving code snippets
- load_neural_retriever function for persistence
- evaluate_retrieval function for benchmarking against ground truth
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

# Import project utilities
from src.data.models import CodeSnippet, RetrievalMethod
from src.lib.utils import set_seed, setup_logging

# Try to import sentence-transformers, fail loudly if missing
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "The 'sentence-transformers' package is required for neural retrieval. "
        "Install it via: pip install sentence-transformers"
    )

# Configure logging
logger = setup_logging(__name__)

# Default model configuration
DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_BATCH_SIZE = 32
DEFAULT_TOP_K = 10
DEFAULT_DEVICE = "cpu"

class NeuralRetriever:
    """
    Dual-encoder retriever using Sentence Transformers.
    
    This retriever encodes code snippets into dense vectors using a 
    pre-trained transformer model and performs similarity search 
    via dot product or cosine similarity.
    
    Attributes:
        model: The SentenceTransformer model instance
        model_name: Name/identifier of the loaded model
        device: Device to run inference on ('cpu' or 'cuda')
        embeddings: Cached embeddings for the indexed corpus (numpy array)
        snippets: List of CodeSnippet objects corresponding to embeddings
        id_map: Mapping from snippet ID to index in embeddings array
        top_k: Default number of results to return
    """
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        device: str = DEFAULT_DEVICE,
        top_k: int = DEFAULT_TOP_K,
        batch_size: int = DEFAULT_BATCH_SIZE
    ):
        """
        Initialize the neural retriever.
        
        Args:
            model_name: HuggingFace model name or path
            device: Device to run on ('cpu' or 'cuda')
            top_k: Default number of retrieval results
            batch_size: Batch size for encoding
        
        Raises:
            RuntimeError: If model fails to load
        """
        self.model_name = model_name
        self.device = device
        self.top_k = top_k
        self.batch_size = batch_size
        self.embeddings: Optional[np.ndarray] = None
        self.snippets: List[CodeSnippet] = []
        self.id_map: Dict[str, int] = {}
        
        logger.info(f"Loading model: {model_name} on {device}")
        try:
            self.model = SentenceTransformer(model_name, device=device)
            logger.info(f"Model loaded successfully: {self.model_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to load SentenceTransformer model: {e}")
    
    def index(self, snippets: List[CodeSnippet]) -> None:
        """
        Index a list of code snippets by encoding them into embeddings.
        
        Args:
            snippets: List of CodeSnippet objects to index
        """
        if not snippets:
            logger.warning("No snippets provided for indexing")
            return
        
        self.snippets = snippets
        self.id_map = {snippet.snippet_id: i for i, snippet in enumerate(snippets)}
        
        # Prepare texts for encoding
        texts = [snippet.processed_text for snippet in snippets]
        
        logger.info(f"Encoding {len(texts)} snippets in batches of {self.batch_size}")
        
        # Encode in batches
        self.embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Normalize embeddings for cosine similarity (optional, but recommended)
        # SentenceTransformer models often output normalized vectors by default
        logger.info(f"Indexing complete. Embedding shape: {self.embeddings.shape}")
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Tuple[CodeSnippet, float]]:
        """
        Retrieve top-k most similar snippets for a given query.
        
        Args:
            query: Natural language query string
            top_k: Number of results to return (defaults to instance top_k)
        
        Returns:
            List of (CodeSnippet, score) tuples sorted by similarity (descending)
        """
        if self.embeddings is None:
            raise RuntimeError("Retriever has not been indexed yet")
        
        k = top_k if top_k is not None else self.top_k
        k = min(k, len(self.snippets))
        
        # Encode query
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            show_progress_bar=False
        )[0]
        
        # Compute similarity scores (dot product)
        # If embeddings are normalized, this equals cosine similarity
        scores = np.dot(self.embeddings, query_embedding)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:k]
        
        # Build results
        results = []
        for idx in top_indices:
            snippet = self.snippets[idx]
            score = float(scores[idx])
            results.append((snippet, score))
        
        return results
    
    def save(self, output_path: Path) -> None:
        """
        Save the retriever state (embeddings and metadata) to disk.
        
        Note: The model itself is not saved, only the embeddings and metadata.
        The model must be reloaded separately when loading.
        
        Args:
            output_path: Directory path to save retriever state
        """
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        state = {
            'model_name': self.model_name,
            'device': self.device,
            'top_k': self.top_k,
            'batch_size': self.batch_size,
            'snippet_count': len(self.snippets),
            'embeddings': self.embeddings,
            'snippets': self.snippets,
            'id_map': self.id_map
        }
        
        state_file = output_path / "neural_retriever_state.pkl"
        with open(state_file, 'wb') as f:
            pickle.dump(state, f)
        
        logger.info(f"Saved neural retriever state to {state_file}")
    
    @classmethod
    def load(cls, state_path: Path) -> 'NeuralRetriever':
        """
        Load a retriever from a saved state file.
        
        Args:
            state_path: Path to the saved state directory/file
        
        Returns:
            NeuralRetriever instance with loaded embeddings
        
        Raises:
            FileNotFoundError: If state file doesn't exist
            RuntimeError: If loading fails
        """
        state_path = Path(state_path)
        
        # Handle both directory and file paths
        if state_path.is_dir():
            state_file = state_path / "neural_retriever_state.pkl"
        else:
            state_file = state_path
        
        if not state_file.exists():
            raise FileNotFoundError(f"State file not found: {state_file}")
        
        logger.info(f"Loading neural retriever from {state_file}")
        
        try:
            with open(state_file, 'rb') as f:
                state = pickle.load(f)
            
            retriever = cls(
                model_name=state['model_name'],
                device=state['device'],
                top_k=state['top_k'],
                batch_size=state['batch_size']
            )
            retriever.embeddings = state['embeddings']
            retriever.snippets = state['snippets']
            retriever.id_map = state['id_map']
            
            logger.info(f"Loaded retriever with {len(retriever.snippets)} snippets")
            return retriever
            
        except Exception as e:
            raise RuntimeError(f"Failed to load retriever state: {e}")


def load_neural_retriever(
    data_dir: Path,
    model_name: str = DEFAULT_MODEL_NAME,
    device: str = DEFAULT_DEVICE,
    top_k: int = DEFAULT_TOP_K
) -> NeuralRetriever:
    """
    Load preprocessed snippets and build a neural retriever.
    
    Args:
        data_dir: Path to processed data directory containing JSONL files
        model_name: SentenceTransformer model name
        device: Device for inference
        top_k: Default top-k for retrieval
    
    Returns:
        Initialized NeuralRetriever with indexed snippets
    """
    data_dir = Path(data_dir)
    
    # Load snippets from JSONL
    snippets = []
    jsonl_file = data_dir / "snippets.jsonl"
    
    if not jsonl_file.exists():
        raise FileNotFoundError(f"Processed data not found: {jsonl_file}")
    
    logger.info(f"Loading snippets from {jsonl_file}")
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            snippet = CodeSnippet(
                snippet_id=data['snippet_id'],
                repo=data.get('repo', ''),
                path=data.get('path', ''),
                original_text=data.get('original_text', ''),
                processed_text=data.get('processed_text', ''),
                language=data.get('language', 'python'),
                is_test=data.get('is_test', False)
            )
            snippets.append(snippet)
    
    logger.info(f"Loaded {len(snippets)} snippets")
    
    # Create and index retriever
    retriever = NeuralRetriever(
        model_name=model_name,
        device=device,
        top_k=top_k
    )
    retriever.index(snippets)
    
    return retriever


def evaluate_retrieval(
    retriever: NeuralRetriever,
    queries_path: Path,
    ground_truth_path: Path,
    k_values: List[int] = [5, 10, 20]
) -> Dict[str, Any]:
    """
    Evaluate retrieval performance against ground truth labels.
    
    Args:
        retriever: Initialized NeuralRetriever instance
        queries_path: Path to queries JSONL file
        ground_truth_path: Path to ground truth labels JSONL file
        k_values: List of k values for @k metrics
    
    Returns:
        Dictionary containing retrieval metrics
    """
    queries_path = Path(queries_path)
    ground_truth_path = Path(ground_truth_path)
    
    # Load queries
    queries = []
    with open(queries_path, 'r', encoding='utf-8') as f:
        for line in f:
            queries.append(json.loads(line))
    
    # Load ground truth
    ground_truth = {}
    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            ground_truth[data['query_id']] = set(data['relevant_snippet_ids'])
    
    logger.info(f"Evaluating on {len(queries)} queries")
    
    # Metrics storage
    all_metrics = {
        'query_results': [],
        'aggregated': {}
    }
    
    for query_data in queries:
        query_id = query_data['query_id']
        query_text = query_data['query_text']
        
        # Retrieve
        results = retriever.retrieve(query_text, top_k=max(k_values))
        
        # Get relevant IDs from ground truth
        relevant_ids = ground_truth.get(query_id, set())
        
        # Compute metrics for each k
        query_metrics = {
            'query_id': query_id,
            'retrieved_ids': [r[0].snippet_id for r in results],
            'scores': [r[1] for r in results],
            'ground_truth': list(relevant_ids),
            'metrics': {}
        }
        
        # Compute precision, recall, ndcg for each k
        for k in k_values:
            retrieved_ids = [r[0].snippet_id for r in results[:k]]
            
            # Precision@k
            hits = len(set(retrieved_ids) & relevant_ids)
            precision = hits / k if k > 0 else 0.0
            
            # Recall@k
            recall = hits / len(relevant_ids) if len(relevant_ids) > 0 else 0.0
            
            # DCG@k
            dcg = 0.0
            for i, rid in enumerate(retrieved_ids):
                if rid in relevant_ids:
                    dcg += 1.0 / np.log2(i + 2)  # i+2 because i is 0-indexed
            
            # IDCG@k
            idcg = 0.0
            num_relevant = min(k, len(relevant_ids))
            for i in range(num_relevant):
                idcg += 1.0 / np.log2(i + 2)
            
            ndcg = dcg / idcg if idcg > 0 else 0.0
            
            query_metrics['metrics'][f'precision@{k}'] = precision
            query_metrics['metrics'][f'recall@{k}'] = recall
            query_metrics['metrics'][f'ndcg@{k}'] = ndcg
        
        all_metrics['query_results'].append(query_metrics)
    
    # Aggregate metrics
    for k in k_values:
        precisions = [q['metrics'][f'precision@{k}'] for q in all_metrics['query_results']]
        recalls = [q['metrics'][f'recall@{k}'] for q in all_metrics['query_results']]
        ndcgs = [q['metrics'][f'ndcg@{k}'] for q in all_metrics['query_results']]
        
        all_metrics['aggregated'][f'precision@{k}'] = float(np.mean(precisions))
        all_metrics['aggregated'][f'recall@{k}'] = float(np.mean(recalls))
        all_metrics['aggregated'][f'ndcg@{k}'] = float(np.mean(ndcgs))
    
    all_metrics['aggregated']['method'] = RetrievalMethod.NEURAL.value
    all_metrics['aggregated']['model_name'] = retriever.model_name
    all_metrics['aggregated']['total_queries'] = len(queries)
    
    logger.info(f"Evaluation complete. Aggregated metrics: {all_metrics['aggregated']}")
    
    return all_metrics


def main():
    """
    Main entry point for standalone neural retriever evaluation.
    
    Usage:
        python -m src.models.retriever_neural --data_dir data/processed/test --output results/neural_eval.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Neural Retriever Evaluation")
    parser.add_argument(
        "--data_dir",
        type=Path,
        default="data/processed/test",
        help="Path to processed data directory"
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default=DEFAULT_MODEL_NAME,
        help="SentenceTransformer model name"
    )
    parser.add_argument(
        "--device",
        type=str,
        default=DEFAULT_DEVICE,
        choices=["cpu", "cuda"],
        help="Device for inference"
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=DEFAULT_TOP_K,
        help="Default top-k for retrieval"
    )
    parser.add_argument(
        "--queries",
        type=Path,
        default=None,
        help="Path to queries JSONL file (defaults to data_dir/queries.jsonl)"
    )
    parser.add_argument(
        "--ground_truth",
        type=Path,
        default=None,
        help="Path to ground truth JSONL file (defaults to data_dir/ground_truth.jsonl)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default="results/neural_retrieval_eval.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Set seed
    set_seed(args.seed)
    
    # Setup paths
    queries_path = args.queries or args.data_dir / "queries.jsonl"
    ground_truth_path = args.ground_truth or args.data_dir / "ground_truth.jsonl"
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load retriever
        logger.info("Loading neural retriever...")
        retriever = load_neural_retriever(
            args.data_dir,
            model_name=args.model_name,
            device=args.device,
            top_k=args.top_k
        )
        
        # Evaluate
        logger.info("Running evaluation...")
        results = evaluate_retrieval(
            retriever,
            queries_path,
            ground_truth_path,
            k_values=[5, 10, 20]
        )
        
        # Save results
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise


if __name__ == "__main__":
    main()
