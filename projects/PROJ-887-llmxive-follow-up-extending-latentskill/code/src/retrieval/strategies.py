"""
Retrieval Strategies for LatentSkill Interpolation.

This module implements the core logic for retrieving skill vectors from the
index and synthesizing new LoRA adapters via various interpolation strategies.
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
SKILL_INDEX_PATH = Path("data/processed/skill_index.npz")
ADAPTERS_OUTPUT_DIR = Path("artifacts/synthesized_adapters")
QUERY_EMBEDDINGS_PATH = Path("data/processed/query_embeddings.npy")
METADATA_PATH = Path("data/processed/skill_metadata.json")

# Ensure output directory exists
ADAPTERS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_skill_index() -> Dict[str, np.ndarray]:
    """
    Load the pre-computed skill index from disk.

    Returns:
        Dict mapping skill names to flattened, normalized weight vectors.

    Raises:
        FileNotFoundError: If the index file does not exist.
    """
    if not SKILL_INDEX_PATH.exists():
        raise FileNotFoundError(
            f"Skill index not found at {SKILL_INDEX_PATH}. "
            "Please run T014b to generate the index first."
        )

    logger.info(f"Loading skill index from {SKILL_INDEX_PATH}")
    data = np.load(SKILL_INDEX_PATH, allow_pickle=True)

    # Convert the numpy dict to a standard Python dict for easier handling
    index = {}
    for key in data.files:
        index[key] = data[key]

    logger.info(f"Loaded {len(index)} skill vectors")
    return index


def load_query_embeddings() -> np.ndarray:
    """
    Load pre-computed query embeddings.

    Returns:
        Numpy array of query embeddings.
    """
    if not QUERY_EMBEDDINGS_PATH.exists():
        raise FileNotFoundError(
            f"Query embeddings not found at {QUERY_EMBEDDINGS_PATH}. "
            "Please run T019 to generate embeddings first."
        )

    logger.info(f"Loading query embeddings from {QUERY_EMBEDDINGS_PATH}")
    return np.load(QUERY_EMBEDDINGS_PATH)


def get_skill_metadata() -> Dict[str, Any]:
    """
    Load metadata associated with each skill in the index.

    Returns:
        Dict containing metadata for each skill (task description, source, etc.).
    """
    # Placeholder for metadata loading logic
    # In a full implementation, this would load from METADATA_PATH
    return {}


def single_nearest_neighbor(
    query_vector: np.ndarray,
    skill_index: Dict[str, np.ndarray],
    top_k: int = 1
) -> List[Tuple[str, float]]:
    """
    Find the single nearest neighbor(s) to the query vector in the skill index.

    Args:
        query_vector: The query embedding vector.
        skill_index: Dictionary of skill name -> flattened weight vector.
        top_k: Number of nearest neighbors to return.

    Returns:
        List of tuples (skill_name, similarity_score) sorted by similarity.
    """
    if not skill_index:
        raise ValueError("Skill index is empty")

    # Normalize query vector
    query_norm = query_vector / np.linalg.norm(query_vector)

    similarities = []
    for skill_name, weight_vector in skill_index.items():
        # Ensure weight vector is normalized (should be from T013)
        weight_norm = weight_vector / np.linalg.norm(weight_vector)
        sim = np.dot(query_norm, weight_norm)
        similarities.append((skill_name, float(sim)))

    # Sort by similarity descending
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]


def unweighted_mean(
    neighbors: List[Tuple[str, float]],
    skill_index: Dict[str, np.ndarray]
) -> np.ndarray:
    """
    Compute the unweighted arithmetic mean of the top-k neighbor weight vectors.

    Args:
        neighbors: List of (skill_name, similarity) tuples.
        skill_index: Dictionary of skill name -> flattened weight vector.

    Returns:
        Averaged weight vector.
    """
    if not neighbors:
        raise ValueError("No neighbors provided for averaging")

    vectors = [skill_index[name] for name, _ in neighbors]
    stacked = np.stack(vectors, axis=0)
    return np.mean(stacked, axis=0)


def cosine_weighted_average(
    neighbors: List[Tuple[str, float]],
    skill_index: Dict[str, np.ndarray]
) -> np.ndarray:
    """
    Compute a cosine-weighted average of the top-k neighbor weight vectors.
    Weights are normalized similarity scores.

    Args:
        neighbors: List of (skill_name, similarity) tuples.
        skill_index: Dictionary of skill name -> flattened weight vector.

    Returns:
        Weighted averaged weight vector.
    """
    if not neighbors:
        raise ValueError("No neighbors provided for averaging")

    names = [name for name, _ in neighbors]
    sims = np.array([sim for _, sim in neighbors])

    # Normalize weights to sum to 1
    weights = sims / np.sum(sims)

    vectors = [skill_index[name] for name in names]
    stacked = np.stack(vectors, axis=0)
    weighted_sum = np.sum(stacked * weights[:, np.newaxis], axis=0)

    # Re-normalize the result vector
    norm = np.linalg.norm(weighted_sum)
    if norm > 0:
        weighted_sum = weighted_sum / norm

    return weighted_sum


def synthesize_adapter(
    query_vector: np.ndarray,
    skill_index: Dict[str, np.ndarray],
    strategy: str = "cosine_weighted",
    top_k: int = 3
) -> np.ndarray:
    """
    Synthesize a new adapter weight vector based on the query and strategy.

    Args:
        query_vector: The query embedding.
        skill_index: The skill vector database.
        strategy: One of "single", "unweighted", "cosine_weighted".
        top_k: Number of neighbors to consider.

    Returns:
        Synthesized weight vector.
    """
    logger.info(f"Synthesizing adapter using strategy: {strategy}, top_k: {top_k}")
    start_time = time.time()

    # Retrieve neighbors
    neighbors = single_nearest_neighbor(query_vector, skill_index, top_k=top_k)
    logger.debug(f"Retrieved {len(neighbors)} neighbors: {[n[0] for n in neighbors]}")

    # Apply strategy
    if strategy == "single":
        result = skill_index[neighbors[0][0]]
    elif strategy == "unweighted":
        result = unweighted_mean(neighbors, skill_index)
    elif strategy == "cosine_weighted":
        result = cosine_weighted_average(neighbors, skill_index)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    elapsed = time.time() - start_time
    logger.info(f"Synthesis completed in {elapsed:.4f} seconds")

    return result


def reconstruct_matrices(
    flat_vector: np.ndarray,
    shape_info: Dict[str, Tuple[int, int]]
) -> Dict[str, np.ndarray]:
    """
    Reconstruct A and B matrices from a flattened vector.

    Args:
        flat_vector: The flattened weight vector.
        shape_info: Dictionary mapping matrix name to (rows, cols).

    Returns:
        Dictionary mapping matrix name to 2D numpy array.
    """
    reconstructed = {}
    current_idx = 0

    for name, (rows, cols) in shape_info.items():
        size = rows * cols
        matrix_flat = flat_vector[current_idx : current_idx + size]
        reconstructed[name] = matrix_flat.reshape((rows, cols))
        current_idx += size

    return reconstructed


def save_synthesized_adapter(
    adapter_vector: np.ndarray,
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save the synthesized adapter vector to disk.

    Args:
        adapter_vector: The synthesized weight vector.
        output_path: Path to save the .npz file.
        metadata: Optional metadata to save with the adapter.
    """
    logger.info(f"Saving synthesized adapter to {output_path}")

    save_dict = {
        'weights': adapter_vector,
        'shape': adapter_vector.shape,
        'is_proxy': False
    }

    if metadata:
        for key, value in metadata.items():
            save_dict[key] = value

    np.savez(output_path, **save_dict)
    logger.info(f"Successfully saved adapter to {output_path}")


def main() -> None:
    """
    Main entry point for running the retrieval and synthesis pipeline.
    This function is intended to be called by scripts/run_t022b.py.
    """
    logger.info("Starting retrieval and synthesis pipeline")

    try:
        # Load data
        skill_index = load_skill_index()
        query_embeddings = load_query_embeddings()

        if len(query_embeddings) == 0:
            logger.warning("No query embeddings found. Exiting.")
            return

        # Process first query as a demo (in real usage, loop over all)
        query = query_embeddings[0]
        logger.info(f"Processing query 0")

        # Synthesize adapter
        synthesized = synthesize_adapter(
            query_vector=query,
            skill_index=skill_index,
            strategy="cosine_weighted",
            top_k=3
        )

        # Save result
        output_file = ADAPTERS_OUTPUT_DIR / "demo_synthesized_adapter.npz"
        save_synthesized_adapter(
            synthesized,
            output_file,
            metadata={"strategy": "cosine_weighted", "top_k": 3}
        )

        logger.info("Pipeline completed successfully")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise