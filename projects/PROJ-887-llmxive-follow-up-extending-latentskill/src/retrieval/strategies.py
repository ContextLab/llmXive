import os
import sys
import logging
import time
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from src.utils.config import get_project_root, get_data_path, get_artifacts_path

logger = logging.getLogger(__name__)

# Constants for edge case handling
MIN_SIMILARITY_THRESHOLD = 0.0
RANDOM_SEED = 42

def load_skill_index(index_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the skill index from the processed data directory.
    
    Args:
        index_path: Optional path to the index file. If None, uses default path.
        
    Returns:
        Dictionary containing the skill index data.
        
    Raises:
        FileNotFoundError: If the index file does not exist.
        ValueError: If the index file is corrupted or empty.
    """
    if index_path is None:
        index_path = str(get_data_path() / "processed" / "skill_index.npz")
    
    path = Path(index_path)
    if not path.exists():
        raise FileNotFoundError(f"Skill index not found at {index_path}")
    
    try:
        data = np.load(path, allow_pickle=True)
        if len(data.files) == 0:
            raise ValueError("Skill index file is empty")
        
        # Extract data from npz
        index_data = {
            'vectors': data['vectors'],
            'metadata': data['metadata'].item() if 'metadata' in data.files else {},
            'ids': data['ids'] if 'ids' in data.files else np.array([])
        }
        
        logger.info(f"Loaded skill index with {len(index_data['vectors'])} vectors")
        return index_data
    except Exception as e:
        raise ValueError(f"Failed to load skill index: {e}")

def load_query_embeddings(embeddings_path: Optional[str] = None) -> np.ndarray:
    """
    Load query embeddings from the processed data directory.
    
    Args:
        embeddings_path: Optional path to the embeddings file. If None, uses default path.
        
    Returns:
        Numpy array of query embeddings.
        
    Raises:
        FileNotFoundError: If the embeddings file does not exist.
    """
    if embeddings_path is None:
        embeddings_path = str(get_data_path() / "processed" / "query_embeddings.npy")
    
    path = Path(embeddings_path)
    if not path.exists():
        raise FileNotFoundError(f"Query embeddings not found at {embeddings_path}")
    
    embeddings = np.load(path)
    logger.info(f"Loaded {len(embeddings)} query embeddings")
    return embeddings

def get_skill_metadata(index_data: Dict[str, Any], skill_id: str) -> Dict[str, Any]:
    """
    Retrieve metadata for a specific skill by ID.
    
    Args:
        index_data: The skill index dictionary.
        skill_id: The ID of the skill to retrieve metadata for.
        
    Returns:
        Dictionary containing the skill's metadata.
        
    Raises:
        KeyError: If the skill_id is not found in the index.
    """
    metadata = index_data.get('metadata', {})
    if skill_id not in metadata:
        raise KeyError(f"Skill ID '{skill_id}' not found in index metadata")
    return metadata[skill_id]

def single_nearest_neighbor(query_vector: np.ndarray, 
                            skill_vectors: np.ndarray,
                            skill_ids: np.ndarray,
                            top_k: int = 1) -> Tuple[List[str], List[float], int]:
    """
    Find the single nearest neighbor (or top-k) using cosine similarity.
    
    Args:
        query_vector: The query embedding vector.
        skill_vectors: Array of skill vectors (shape: n_skills x dim).
        skill_ids: Array of skill IDs corresponding to the vectors.
        top_k: Number of neighbors to return (default 1).
        
    Returns:
        Tuple of (list of skill IDs, list of similarity scores, index of best match).
        
    Raises:
        ValueError: If query vector dimension doesn't match skill vectors.
    """
    if query_vector.ndim == 1:
        query_vector = query_vector.reshape(1, -1)
    
    if query_vector.shape[1] != skill_vectors.shape[1]:
        raise ValueError(f"Query vector dimension {query_vector.shape[1]} does not match skill vectors dimension {skill_vectors.shape[1]}")
    
    # Compute cosine similarity
    query_norm = np.linalg.norm(query_vector, axis=1, keepdims=True)
    skill_norms = np.linalg.norm(skill_vectors, axis=1, keepdims=True)
    
    # Handle zero-norm vectors
    query_norm[query_norm == 0] = 1
    skill_norms[skill_norms == 0] = 1
    
    query_normalized = query_vector / query_norm
    skill_normalized = skill_vectors / skill_norms
    
    similarities = np.dot(skill_normalized, query_normalized.T).flatten()
    
    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]
    top_ids = [str(skill_ids[i]) for i in top_indices]
    top_scores = [float(similarities[i]) for i in top_indices]
    
    best_index = int(top_indices[0])
    
    logger.info(f"Single nearest neighbor: top skill '{top_ids[0]}' with similarity {top_scores[0]:.4f}")
    return top_ids, top_scores, best_index

def unweighted_mean(query_vector: np.ndarray,
                   skill_vectors: np.ndarray,
                   skill_ids: np.ndarray,
                   top_k: int = 3) -> Tuple[np.ndarray, List[str], List[float]]:
    """
    Compute unweighted arithmetic mean of top-k skill vectors.
    
    Args:
        query_vector: The query embedding vector.
        skill_vectors: Array of skill vectors.
        skill_ids: Array of skill IDs.
        top_k: Number of top skills to average.
        
    Returns:
        Tuple of (mean vector, list of skill IDs used, list of similarity scores).
        
    Raises:
        ValueError: If top_k is greater than number of available skills.
    """
    if top_k > len(skill_vectors):
        raise ValueError(f"top_k ({top_k}) exceeds number of available skills ({len(skill_vectors)})")
    
    _, top_scores, _ = single_nearest_neighbor(query_vector, skill_vectors, skill_ids, top_k)
    
    # Get indices of top-k
    query_norm = np.linalg.norm(query_vector, axis=1, keepdims=True)
    skill_norms = np.linalg.norm(skill_vectors, axis=1, keepdims=True)
    query_norm[query_norm == 0] = 1
    skill_norms[skill_norms == 0] = 1
    
    query_normalized = query_vector / query_norm
    skill_normalized = skill_vectors / skill_norms
    similarities = np.dot(skill_normalized, query_normalized.T).flatten()
    
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    # Compute unweighted mean
    mean_vector = np.mean(skill_vectors[top_indices], axis=0)
    
    top_ids = [str(skill_ids[i]) for i in top_indices]
    
    logger.info(f"Unweighted mean of {top_k} skills: {', '.join(top_ids)}")
    return mean_vector, top_ids, top_scores

def cosine_weighted_average(query_vector: np.ndarray,
                           skill_vectors: np.ndarray,
                           skill_ids: np.ndarray,
                           top_k: int = 3) -> Tuple[np.ndarray, List[str], List[float]]:
    """
    Compute cosine-weighted average of top-k skill vectors.
    
    Args:
        query_vector: The query embedding vector.
        skill_vectors: Array of skill vectors.
        skill_ids: Array of skill IDs.
        top_k: Number of top skills to weight.
        
    Returns:
        Tuple of (weighted mean vector, list of skill IDs used, list of similarity scores).
        
    Raises:
        ValueError: If top_k is greater than number of available skills.
    """
    if top_k > len(skill_vectors):
        raise ValueError(f"top_k ({top_k}) exceeds number of available skills ({len(skill_vectors)})")
    
    # Compute similarities
    query_norm = np.linalg.norm(query_vector, axis=1, keepdims=True)
    skill_norms = np.linalg.norm(skill_vectors, axis=1, keepdims=True)
    query_norm[query_norm == 0] = 1
    skill_norms[skill_norms == 0] = 1
    
    query_normalized = query_vector / query_norm
    skill_normalized = skill_vectors / skill_norms
    similarities = np.dot(skill_normalized, query_normalized.T).flatten()
    
    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]
    top_similarities = similarities[top_indices]
    
    # Handle edge case: identical similarity scores (random tie-breaking)
    if len(np.unique(top_similarities)) == 1 and len(top_similarities) > 1:
        logger.warning("Identical similarity scores detected. Using weighted average with uniform weights.")
        # Random tie-breaking by shuffling indices
        np.random.seed(RANDOM_SEED)
        shuffle_indices = np.random.permutation(len(top_indices))
        top_indices = top_indices[shuffle_indices]
        top_similarities = top_similarities[shuffle_indices]
    
    # Normalize weights
    weights = top_similarities / np.sum(top_similarities)
    
    # Compute weighted average
    weighted_vector = np.zeros_like(skill_vectors[0])
    for i, idx in enumerate(top_indices):
        weighted_vector += weights[i] * skill_vectors[idx]
    
    top_ids = [str(skill_ids[i]) for i in top_indices]
    top_scores = [float(top_similarities[i]) for i in range(len(top_indices))]
    
    logger.info(f"Cosine-weighted average of {top_k} skills: {', '.join(top_ids)}")
    return weighted_vector, top_ids, top_scores

def synthesize_adapter(query_vector: np.ndarray,
                      strategy: str,
                      skill_vectors: np.ndarray,
                      skill_ids: np.ndarray,
                      top_k: int = 3) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Synthesize a skill vector using the specified strategy.
    
    Args:
        query_vector: The query embedding vector.
        strategy: One of 'nearest', 'mean', or 'weighted'.
        skill_vectors: Array of skill vectors.
        skill_ids: Array of skill IDs.
        top_k: Number of skills to consider (for mean/weighted).
        
    Returns:
        Tuple of (synthesized vector, metadata dictionary).
        
    Raises:
        ValueError: If strategy is invalid or query is out-of-distribution.
    """
    start_time = time.time()
    
    # Check for out-of-distribution query (very low similarity to all skills)
    query_norm = np.linalg.norm(query_vector, axis=1, keepdims=True)
    skill_norms = np.linalg.norm(skill_vectors, axis=1, keepdims=True)
    query_norm[query_norm == 0] = 1
    skill_norms[skill_norms == 0] = 1
    
    query_normalized = query_vector / query_norm
    skill_normalized = skill_vectors / skill_norms
    similarities = np.dot(skill_normalized, query_normalized.T).flatten()
    
    max_similarity = np.max(similarities)
    if max_similarity < MIN_SIMILARITY_THRESHOLD:
        raise ValueError(f"Query is out-of-distribution: max similarity {max_similarity:.4f} below threshold {MIN_SIMILARITY_THRESHOLD}")
    
    synthesized_vector = None
    metadata = {}
    
    if strategy == 'nearest':
        _, scores, _ = single_nearest_neighbor(query_vector, skill_vectors, skill_ids, top_k=1)
        synthesized_vector, _, _ = single_nearest_neighbor(query_vector, skill_vectors, skill_ids, top_k=1)
        metadata = {
            'strategy': 'nearest',
            'top_skills': [str(skill_ids[np.argmax(similarities)])],
            'similarity_scores': [float(scores[0])]
        }
    elif strategy == 'mean':
        synthesized_vector, top_ids, scores = unweighted_mean(query_vector, skill_vectors, skill_ids, top_k)
        metadata = {
            'strategy': 'mean',
            'top_skills': top_ids,
            'similarity_scores': scores,
            'top_k': top_k
        }
    elif strategy == 'weighted':
        synthesized_vector, top_ids, scores = cosine_weighted_average(query_vector, skill_vectors, skill_ids, top_k)
        metadata = {
            'strategy': 'weighted',
            'top_skills': top_ids,
            'similarity_scores': scores,
            'top_k': top_k
        }
    else:
        raise ValueError(f"Invalid strategy: {strategy}. Must be 'nearest', 'mean', or 'weighted'.")
    
    elapsed_time = time.time() - start_time
    metadata['latency_ms'] = elapsed_time * 1000
    metadata['query_max_similarity'] = float(max_similarity)
    
    logger.info(f"Synthesis completed with strategy '{strategy}' in {elapsed_time*1000:.2f}ms")
    return synthesized_vector, metadata

def reconstruct_matrices(synthesized_vector: np.ndarray,
                        original_shape: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reconstruct A and B matrices from a flattened synthesized vector.
    
    Args:
        synthesized_vector: The flattened synthesized vector.
        original_shape: The original (in_features, out_features) shape.
        
    Returns:
        Tuple of (A_matrix, B_matrix).
        
    Raises:
        ValueError: If vector length doesn't match expected shape.
    """
    in_features, out_features = original_shape
    expected_length = in_features * out_features
    
    if len(synthesized_vector) != expected_length:
        raise ValueError(f"Vector length {len(synthesized_vector)} does not match expected {expected_length}")
    
    # Reshape to original matrix shape
    combined_matrix = synthesized_vector.reshape(in_features, out_features)
    
    # For LoRA, we typically have two matrices A and B
    # Assuming the vector was formed by concatenating flattened A and B
    # If the vector represents the product AB, we need to factorize
    # For simplicity, we assume the vector is the flattened combined weight
    # and we split it into two equal parts if possible, or return as combined
    
    # If the vector is meant to be a single matrix (combined), reshape directly
    # If it's two matrices, we need to know the split point
    # Assuming equal split for now
    if len(synthesized_vector) % 2 == 0:
        mid = len(synthesized_vector) // 2
        A_flat = synthesized_vector[:mid]
        B_flat = synthesized_vector[mid:]
        
        # Reshape to reasonable dimensions (assuming square or proportional)
        A_shape = (in_features, out_features // 2) if out_features > 1 else (in_features, 1)
        B_shape = (out_features // 2, out_features) if out_features > 1 else (1, out_features)
        
        if len(A_flat) == A_shape[0] * A_shape[1] and len(B_flat) == B_shape[0] * B_shape[1]:
            A_matrix = A_flat.reshape(A_shape)
            B_matrix = B_flat.reshape(B_shape)
        else:
            # Fallback: reshape to original dimensions
            A_matrix = combined_matrix
            B_matrix = np.eye(out_features)
    else:
        # Odd length, treat as single matrix
        A_matrix = combined_matrix
        B_matrix = np.eye(out_features)
    
    return A_matrix, B_matrix

def save_synthesized_adapter(A_matrix: np.ndarray,
                            B_matrix: np.ndarray,
                            output_path: str,
                            metadata: Dict[str, Any]) -> None:
    """
    Save synthesized LoRA adapter matrices to disk.
    
    Args:
        A_matrix: The A matrix.
        B_matrix: The B matrix.
        output_path: Path to save the adapter file.
        metadata: Metadata dictionary to include in the file.
        
    Raises:
        IOError: If the file cannot be written.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        np.savez(str(output_path),
                A=A_matrix,
                B=B_matrix,
                metadata=metadata)
        logger.info(f"Saved synthesized adapter to {output_path}")
    except Exception as e:
        raise IOError(f"Failed to save synthesized adapter: {e}")

def main():
    """
    Main entry point for the strategies module.
    Demonstrates the synthesis pipeline with example data.
    """
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Load skill index
        index_data = load_skill_index()
        skill_vectors = index_data['vectors']
        skill_ids = index_data['ids']
        
        # Create a sample query vector (in practice, this would come from query.py)
        np.random.seed(RANDOM_SEED)
        sample_query = np.random.randn(skill_vectors.shape[1])
        
        logger.info(f"Testing synthesis strategies with {len(skill_vectors)} skills")
        
        # Test single nearest neighbor
        logger.info("\n--- Single Nearest Neighbor ---")
        _, scores, _ = single_nearest_neighbor(sample_query, skill_vectors, skill_ids, top_k=1)
        logger.info(f"Best match similarity: {scores[0]:.4f}")
        
        # Test unweighted mean
        logger.info("\n--- Unweighted Mean (k=3) ---")
        mean_vec, top_ids, scores = unweighted_mean(sample_query, skill_vectors, skill_ids, top_k=3)
        logger.info(f"Used skills: {top_ids}")
        logger.info(f"Similarity scores: {scores}")
        
        # Test cosine-weighted average
        logger.info("\n--- Cosine-Weighted Average (k=3) ---")
        weighted_vec, top_ids, scores = cosine_weighted_average(sample_query, skill_vectors, skill_ids, top_k=3)
        logger.info(f"Used skills: {top_ids}")
        logger.info(f"Similarity scores: {scores}")
        
        # Test full synthesis pipeline
        logger.info("\n--- Full Synthesis Pipeline ---")
        for strategy in ['nearest', 'mean', 'weighted']:
            logger.info(f"\nTesting strategy: {strategy}")
            try:
                synthesized, metadata = synthesize_adapter(
                    sample_query, 
                    strategy, 
                    skill_vectors, 
                    skill_ids, 
                    top_k=3
                )
                logger.info(f"  Strategy: {metadata['strategy']}")
                logger.info(f"  Latency: {metadata['latency_ms']:.2f}ms")
                logger.info(f"  Top skills: {', '.join(metadata['top_skills'])}")
                
                # Reconstruct matrices (assuming original shape)
                A, B = reconstruct_matrices(synthesized, (4096, 1024))
                logger.info(f"  Reconstructed A shape: {A.shape}, B shape: {B.shape}")
                
            except ValueError as e:
                logger.error(f"  Error: {e}")
        
        logger.info("\nAll synthesis strategies tested successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        logger.error("Please ensure T014d has been executed to generate the skill index.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()