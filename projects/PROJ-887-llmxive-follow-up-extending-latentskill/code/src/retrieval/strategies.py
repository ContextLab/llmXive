import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data"
PROCESSED_PATH = DATA_PATH / "processed"
SKILL_INDEX_PATH = PROCESSED_PATH / "skill_index.npz"

def load_skill_index(index_path: Optional[Path] = None) -> Dict[str, np.ndarray]:
    """
    Load the flattened skill index from disk.

    Args:
        index_path: Path to the skill index file. Defaults to SKILL_INDEX_PATH.

    Returns:
        Dictionary containing 'vectors', 'metadata', and 'ids'.
    """
    if index_path is None:
        index_path = SKILL_INDEX_PATH

    if not index_path.exists():
        raise FileNotFoundError(f"Skill index not found at {index_path}")

    logger.info(f"Loading skill index from {index_path}")
    data = np.load(index_path, allow_pickle=True)
    
    # Convert numpy arrays to lists if necessary for compatibility
    vectors = data['vectors']
    metadata = data['metadata']
    ids = data['ids']
    
    return {
        'vectors': vectors,
        'metadata': metadata,
        'ids': ids
    }

def load_query_embeddings(query_path: Path) -> np.ndarray:
    """
    Load query embeddings from a file.

    Args:
        query_path: Path to the query embeddings file.

    Returns:
        Numpy array of query embeddings.
    """
    if not query_path.exists():
        raise FileNotFoundError(f"Query embeddings not found at {query_path}")
    
    logger.info(f"Loading query embeddings from {query_path}")
    return np.load(query_path)

def get_skill_metadata(skill_index: Dict[str, np.ndarray]) -> List[Dict[str, Any]]:
    """
    Extract metadata from the skill index.

    Args:
        skill_index: The loaded skill index dictionary.

    Returns:
        List of metadata dictionaries.
    """
    return skill_index['metadata'].tolist() if isinstance(skill_index['metadata'], np.ndarray) else skill_index['metadata']

def single_nearest_neighbor(query_vector: np.ndarray, skill_index: Dict[str, np.ndarray], top_k: int = 1) -> List[Tuple[int, float, np.ndarray]]:
    """
    Find the single nearest neighbor to the query vector.

    Args:
        query_vector: The query embedding vector.
        skill_index: The loaded skill index.
        top_k: Number of neighbors to return (default 1).

    Returns:
        List of tuples (index, similarity, vector).
    """
    vectors = skill_index['vectors']
    
    # Calculate cosine similarity
    # Normalize vectors
    query_norm = query_vector / np.linalg.norm(query_vector)
    vectors_norm = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    
    similarities = np.dot(vectors_norm, query_norm)
    
    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        results.append((int(idx), float(similarities[idx]), vectors[idx]))
    
    return results

def unweighted_mean(retrieved_vectors: List[np.ndarray]) -> np.ndarray:
    """
    Compute the unweighted arithmetic mean of retrieved vectors.

    Args:
        retrieved_vectors: List of retrieved vectors.

    Returns:
        Mean vector.
    """
    if not retrieved_vectors:
        raise ValueError("Cannot compute mean of empty list")
    
    return np.mean(retrieved_vectors, axis=0)

def cosine_weighted_average(retrieved: List[Tuple[int, float, np.ndarray]]) -> np.ndarray:
    """
    Compute the cosine-weighted average of retrieved vectors.

    Args:
        retrieved: List of tuples (index, similarity, vector).

    Returns:
        Weighted average vector.
    """
    if not retrieved:
        raise ValueError("Cannot compute weighted average of empty list")
    
    weights = np.array([sim for _, sim, _ in retrieved])
    vectors = np.array([vec for _, _, vec in retrieved])
    
    # Normalize weights
    weights_sum = np.sum(weights)
    if weights_sum == 0:
        # Fallback to uniform weights if sum is zero
        weights = np.ones(len(weights)) / len(weights)
    else:
        weights = weights / weights_sum
    
    return np.dot(weights, vectors)

def synthesize_adapter(retrieved: List[Tuple[int, float, np.ndarray]], strategy: str = "weighted") -> np.ndarray:
    """
    Synthesize an adapter vector based on the retrieval strategy.

    Args:
        retrieved: List of retrieved (index, similarity, vector) tuples.
        strategy: Strategy to use ("mean" or "weighted").

    Returns:
        Synthesized adapter vector.
    """
    if not retrieved:
        raise ValueError("No retrieved vectors to synthesize adapter")
    
    vectors = [vec for _, _, vec in retrieved]
    
    if strategy == "mean":
        return unweighted_mean(vectors)
    elif strategy == "weighted":
        return cosine_weighted_average(retrieved)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

def reconstruct_matrices(synthesized_vector: np.ndarray, original_shape: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reconstruct A and B matrices from the synthesized vector.

    Args:
        synthesized_vector: The synthesized 1D vector.
        original_shape: The original (rows, cols) shape of the matrices.

    Returns:
        Tuple of (A_matrix, B_matrix).
    """
    total_size = synthesized_vector.size
    if total_size % 2 != 0:
        raise ValueError("Synthesized vector size must be even for A and B matrices")
    
    half_size = total_size // 2
    A = synthesized_vector[:half_size].reshape(original_shape)
    B = synthesized_vector[half_size:].reshape(original_shape)
    
    return A, B

def save_synthesized_adapter(A: np.ndarray, B: np.ndarray, output_path: Path, metadata: Dict[str, Any]) -> None:
    """
    Save the synthesized adapter matrices to disk.

    Args:
        A: The A matrix.
        B: The B matrix.
        output_path: Path to save the adapter.
        metadata: Metadata dictionary to save with the adapter.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    np.savez(output_path, A=A, B=B, metadata=metadata)
    logger.info(f"Saved synthesized adapter to {output_path}")

def main():
    """
    Main entry point for the strategies module.
    Demonstrates retrieval and synthesis with empty result handling.
    """
    # Load skill index
    try:
        skill_index = load_skill_index()
    except FileNotFoundError as e:
        logger.error(str(e))
        return

    # Create a dummy query vector (random for demonstration)
    # In real usage, this would come from an embedding model
    query_vector = np.random.randn(skill_index['vectors'].shape[1])
    
    # Test with a very large k to potentially trigger empty result handling
    # (though in a real index, this would just return fewer items)
    k = 1000
    
    logger.info(f"Attempting to retrieve top-{k} neighbors...")
    
    # Perform retrieval
    retrieved = single_nearest_neighbor(query_vector, skill_index, top_k=k)
    
    # Handle empty result set case
    if len(retrieved) < k:
        logger.warning(f"Insufficient neighbors retrieved (k={k}, found={len(retrieved)})")
    
    if not retrieved:
        logger.error("No neighbors found. Cannot synthesize adapter.")
        return
    
    # Synthesize adapter
    synthesized_vector = synthesize_adapter(retrieved, strategy="weighted")
    
    # Reconstruct matrices (assuming original shape based on vector size)
    # This is a simplification; real implementation would need actual shape info
    # For demonstration, we'll use a square matrix assumption
    dim = int(np.sqrt(synthesized_vector.size * 2))
    if dim * dim * 2 != synthesized_vector.size:
        # Fallback: use half size for A and B
        dim = synthesized_vector.size // 2
        A_shape = (dim, 1)
        B_shape = (1, dim)
    else:
        A_shape = (dim, dim)
        B_shape = (dim, dim)
    
    A, B = reconstruct_matrices(synthesized_vector, A_shape)
    
    # Save result
    output_path = PROCESSED_PATH / "synthesized_adapter.npz"
    save_synthesized_adapter(A, B, output_path, {
        "query_vector_shape": query_vector.shape,
        "retrieved_count": len(retrieved),
        "requested_k": k,
        "strategy": "weighted"
    })

if __name__ == "__main__":
    main()