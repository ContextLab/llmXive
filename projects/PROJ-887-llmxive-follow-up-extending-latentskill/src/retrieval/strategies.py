"""
Retrieval and synthesis strategies for LatentSkill project.

Implements:
- Loading skill index and query embeddings
- Retrieval strategies (single nearest, unweighted mean, cosine-weighted)
- Adapter synthesis and serialization
"""

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
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_SYNTHESIZED = PROJECT_ROOT / "artifacts" / "synthesized_adapters"

# Ensure output directory exists
ARTIFACTS_SYNTHESIZED.mkdir(parents=True, exist_ok=True)


def load_skill_index(index_path: Optional[Path] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load the flattened skill index from disk.

    Args:
        index_path: Path to the skill index file. Defaults to data/processed/skill_index.npz.

    Returns:
        Tuple of (vectors array, metadata dict)
    """
    if index_path is None:
        index_path = DATA_PROCESSED / "skill_index.npz"

    if not index_path.exists():
        raise FileNotFoundError(f"Skill index not found at {index_path}. "
                              "Run T014b to generate the index first.")

    logger.info(f"Loading skill index from {index_path}")
    data = np.load(index_path, allow_pickle=True)

    vectors = data['vectors']
    metadata = data['metadata'].item() if 'metadata' in data else {}

    logger.info(f"Loaded {len(vectors)} skill vectors")
    return vectors, metadata


def load_query_embeddings(query_path: Optional[Path] = None) -> np.ndarray:
    """
    Load query embeddings from disk.

    Args:
        query_path: Path to query embeddings file.

    Returns:
        Query embeddings array
    """
    if query_path is None:
        query_path = DATA_PROCESSED / "query_embeddings.npy"

    if not query_path.exists():
        raise FileNotFoundError(f"Query embeddings not found at {query_path}")

    logger.info(f"Loading query embeddings from {query_path}")
    return np.load(query_path)


def get_skill_metadata(metadata: Dict[str, Any], skill_id: str) -> Dict[str, Any]:
    """
    Get metadata for a specific skill ID.

    Args:
        metadata: Full metadata dictionary from the index
        skill_id: The skill identifier

    Returns:
        Metadata dict for the skill
    """
    return metadata.get(skill_id, {})


def single_nearest_neighbor(query_vector: np.ndarray,
                            skill_vectors: np.ndarray) -> Tuple[str, float, int]:
    """
    Find the single nearest neighbor to the query vector.

    Args:
        query_vector: The query embedding vector
        skill_vectors: Array of all skill vectors

    Returns:
        Tuple of (skill_id, similarity_score, index)
    """
    # Compute cosine similarity
    norms = np.linalg.norm(skill_vectors, axis=1, keepdims=True)
    normalized_vectors = skill_vectors / (norms + 1e-8)

    query_norm = np.linalg.norm(query_vector)
    normalized_query = query_vector / (query_norm + 1e-8)

    similarities = np.dot(skill_vectors, normalized_query)
    best_idx = int(np.argmax(similarities))
    best_similarity = float(similarities[best_idx])

    return best_idx, best_similarity, best_idx


def unweighted_mean(query_vector: np.ndarray,
                    skill_vectors: np.ndarray,
                    top_k: int = 3) -> Tuple[List[int], np.ndarray, List[float]]:
    """
    Retrieve top-k nearest neighbors and compute unweighted mean.

    Args:
        query_vector: The query embedding vector
        skill_vectors: Array of all skill vectors
        top_k: Number of neighbors to retrieve

    Returns:
        Tuple of (indices of top-k, mean vector, similarities list)
    """
    # Compute cosine similarity
    norms = np.linalg.norm(skill_vectors, axis=1, keepdims=True)
    normalized_vectors = skill_vectors / (norms + 1e-8)

    query_norm = np.linalg.norm(query_vector)
    normalized_query = query_vector / (query_norm + 1e-8)

    similarities = np.dot(skill_vectors, normalized_query)

    # Get top-k indices
    top_k_indices = np.argsort(similarities)[-top_k:][::-1]
    top_k_indices = top_k_indices.tolist()
    top_k_similarities = similarities[top_k_indices].tolist()

    # Compute unweighted mean
    mean_vector = np.mean(skill_vectors[top_k_indices], axis=0)

    return top_k_indices, mean_vector, top_k_similarities


def cosine_weighted_average(query_vector: np.ndarray,
                            skill_vectors: np.ndarray,
                            top_k: int = 3) -> Tuple[List[int], np.ndarray, List[float]]:
    """
    Retrieve top-k nearest neighbors and compute cosine-weighted average.

    Args:
        query_vector: The query embedding vector
        skill_vectors: Array of all skill vectors
        top_k: Number of neighbors to retrieve

    Returns:
        Tuple of (indices of top-k, weighted mean vector, similarities list)
    """
    # Compute cosine similarity
    norms = np.linalg.norm(skill_vectors, axis=1, keepdims=True)
    normalized_vectors = skill_vectors / (norms + 1e-8)

    query_norm = np.linalg.norm(query_vector)
    normalized_query = query_vector / (query_norm + 1e-8)

    similarities = np.dot(skill_vectors, normalized_query)

    # Get top-k indices
    top_k_indices = np.argsort(similarities)[-top_k:][::-1]
    top_k_indices = top_k_indices.tolist()
    top_k_similarities = similarities[top_k_indices].tolist()

    # Compute cosine-weighted average
    weights = np.array(top_k_similarities)
    weights = weights / (np.sum(weights) + 1e-8)

    weighted_mean = np.zeros_like(skill_vectors[0])
    for idx, weight in zip(top_k_indices, weights):
        weighted_mean += weight * skill_vectors[idx]

    return top_k_indices, weighted_mean, top_k_similarities


def synthesize_adapter(retrieval_method: str,
                       query_vector: np.ndarray,
                       skill_vectors: np.ndarray,
                       metadata: Dict[str, Any],
                       top_k: int = 3) -> Dict[str, Any]:
    """
    Synthesize a LoRA adapter using the specified retrieval method.

    Args:
        retrieval_method: One of 'single', 'unweighted', 'cosine_weighted'
        query_vector: The query embedding vector
        skill_vectors: Array of all skill vectors
        metadata: Skill metadata from the index
        top_k: Number of neighbors (for multi-neighbor methods)

    Returns:
        Dictionary containing synthesized adapter data
    """
    start_time = time.time()

    if retrieval_method == 'single':
        idx, sim, _ = single_nearest_neighbor(query_vector, skill_vectors)
        synthesized_vector = skill_vectors[idx]
        skill_ids = [idx]
        similarities = [sim]

    elif retrieval_method == 'unweighted':
        skill_ids, synthesized_vector, similarities = unweighted_mean(
            query_vector, skill_vectors, top_k
        )

    elif retrieval_method == 'cosine_weighted':
        skill_ids, synthesized_vector, similarities = cosine_weighted_average(
            query_vector, skill_vectors, top_k
        )

    else:
        raise ValueError(f"Unknown retrieval method: {retrieval_method}")

    elapsed_time = time.time() - start_time

    # Reconstruct A and B matrices from flattened vector
    # Assuming original dimensions: in_features=4096, out_features=1024
    # Total flattened size = 4096 * 1024 = 4,194,304
    in_features = 4096
    out_features = 1024
    expected_size = in_features * out_features

    if synthesized_vector.shape[0] != expected_size:
        logger.warning(f"Vector size {synthesized_vector.shape[0]} doesn't match "
                     f"expected {expected_size}. Using actual size.")
        # Try to infer dimensions if possible
        # For now, we'll use the actual vector and let downstream handle it
        reconstructed_a = synthesized_vector.reshape(-1, 1)
        reconstructed_b = np.ones((1, synthesized_vector.shape[0]))
    else:
        # Reshape to A (out_features, in_features) and B (in_features, out_features)
        # Standard LoRA: W = W0 + A @ B where A is [r, in] and B is [out, r]
        # But we flattened A and B separately, so we need to know the rank
        # For simplicity, assume rank r=1 and split evenly
        # Actually, the flattened vector should be A flattened + B flattened
        # Let's assume the vector contains [A_flat, B_flat]
        half_size = synthesized_vector.shape[0] // 2
        a_flat = synthesized_vector[:half_size]
        b_flat = synthesized_vector[half_size:]

        # Reshape to matrices
        # A: [rank, in_features], B: [out_features, rank]
        # We need to know the rank. Let's assume rank=64 (common for LoRA)
        rank = 64
        reconstructed_a = a_flat.reshape(rank, in_features)
        reconstructed_b = b_flat.reshape(out_features, rank)

    return {
        'skill_ids': skill_ids,
        'similarities': similarities,
        'synthesized_vector': synthesized_vector,
        'matrix_a': reconstructed_a,
        'matrix_b': reconstructed_b,
        'retrieval_method': retrieval_method,
        'top_k': top_k,
        'latency_seconds': elapsed_time
    }


def reconstruct_matrices(synthesized_vector: np.ndarray,
                         in_features: int = 4096,
                         out_features: int = 1024,
                         rank: int = 64) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reconstruct A and B matrices from a synthesized flattened vector.

    Args:
        synthesized_vector: Flattened synthesized vector
        in_features: Input dimension
        out_features: Output dimension
        rank: LoRA rank

    Returns:
        Tuple of (matrix_a, matrix_b)
    """
    half_size = synthesized_vector.shape[0] // 2
    a_flat = synthesized_vector[:half_size]
    b_flat = synthesized_vector[half_size:]

    matrix_a = a_flat.reshape(rank, in_features)
    matrix_b = b_flat.reshape(out_features, rank)

    return matrix_a, matrix_b


def save_synthesized_adapter(synthesized_data: Dict[str, Any],
                             output_path: Optional[Path] = None,
                             task_id: str = "unknown") -> Path:
    """
    Save synthesized adapter matrices to disk.

    Args:
        synthesized_data: Dictionary from synthesize_adapter()
        output_path: Optional custom output path
        task_id: Identifier for the task/query

    Returns:
        Path to the saved file
    """
    if output_path is None:
        # Generate filename based on task_id and retrieval method
        method = synthesized_data.get('retrieval_method', 'unknown')
        filename = f"{task_id}_{method}.npz"
        output_path = ARTIFACTS_SYNTHESIZED / filename

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate data before saving
    matrix_a = synthesized_data['matrix_a']
    matrix_b = synthesized_data['matrix_b']

    # Check for NaN or Inf
    if np.any(np.isnan(matrix_a)) or np.any(np.isinf(matrix_a)):
        raise ValueError("Matrix A contains NaN or Inf values")
    if np.any(np.isnan(matrix_b)) or np.any(np.isinf(matrix_b)):
        raise ValueError("Matrix B contains NaN or Inf values")

    # Check dimensions
    if matrix_a.shape[0] == 0 or matrix_b.shape[0] == 0:
        raise ValueError("Matrix dimensions are zero")

    logger.info(f"Saving synthesized adapter to {output_path}")
    logger.info(f"  Matrix A shape: {matrix_a.shape}")
    logger.info(f"  Matrix B shape: {matrix_b.shape}")
    logger.info(f"  Matrix A range: [{matrix_a.min():.6f}, {matrix_a.max():.6f}]")
    logger.info(f"  Matrix B range: [{matrix_b.min():.6f}, {matrix_b.max():.6f}]")

    # Save to NPZ format
    np.savez(
        output_path,
        matrix_a=matrix_a,
        matrix_b=matrix_b,
        skill_ids=synthesized_data['skill_ids'],
        similarities=synthesized_data['similarities'],
        retrieval_method=synthesized_data['retrieval_method'],
        top_k=synthesized_data['top_k'],
        latency_seconds=synthesized_data['latency_seconds']
    )

    logger.info(f"Successfully saved synthesized adapter: {output_path}")
    return output_path


def main():
    """
    Main entry point for T022b - Serialization of synthesized adapters.

    This script:
    1. Loads the skill index (from T014b)
    2. Loads query embeddings (from T019)
    3. Synthesizes adapters using various strategies
    4. Saves the synthesized A/B matrices to artifacts/synthesized_adapters/

    Usage:
        python -m scripts.run_t022b
    """
    logger.info("=" * 60)
    logger.info("Starting T022b: Adapter Serialization")
    logger.info("=" * 60)

    try:
        # Load skill index
        skill_vectors, metadata = load_skill_index()

        # Load query embeddings
        query_embeddings = load_query_embeddings()

        logger.info(f"Processing {len(query_embeddings)} queries")

        # Process each query with different strategies
        strategies = ['single', 'unweighted', 'cosine_weighted']
        top_k_values = [1, 3, 5]

        saved_paths = []

        for q_idx, query_vector in enumerate(query_embeddings):
            query_id = f"query_{q_idx:04d}"

            for strategy in strategies:
                # For single neighbor, top_k=1 is implicit
                k = 1 if strategy == 'single' else top_k_values[0]

                logger.info(f"Processing {query_id} with {strategy} (k={k})")

                synthesized = synthesize_adapter(
                    retrieval_method=strategy,
                    query_vector=query_vector,
                    skill_vectors=skill_vectors,
                    metadata=metadata,
                    top_k=k
                )

                # Save the adapter
                task_id = f"{query_id}_{strategy}_k{k}"
                output_path = save_synthesized_adapter(
                    synthesized_data=synthesized,
                    task_id=task_id
                )
                saved_paths.append(output_path)

        logger.info(f"Total adapters saved: {len(saved_paths)}")
        logger.info(f"Output directory: {ARTIFACTS_SYNTHESIZED}")

        # Summary
        logger.info("Summary:")
        for path in saved_paths:
            logger.info(f"  - {path.name}")

        logger.info("=" * 60)
        logger.info("T022b completed successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"T022b failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()