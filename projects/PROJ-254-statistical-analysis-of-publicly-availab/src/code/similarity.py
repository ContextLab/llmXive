import os
import logging
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

from utils import get_logger, setup_logging, set_deterministic_seed
from memory_utils import monitor_and_maybe_gc

def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        vec1: First vector.
        vec2: Second vector.

    Returns:
        Cosine similarity value.
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

def compute_pairwise_similarities(embeddings: Dict[str, np.ndarray]) -> np.ndarray:
    """
    Compute pairwise cosine similarity matrix for embeddings.

    Args:
        embeddings: Dictionary mapping genre names to embeddings.

    Returns:
        Symmetric similarity matrix.
    """
    genres = list(embeddings.keys())
    n = len(genres)
    similarity_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i == j:
                similarity_matrix[i, j] = 1.0
            elif j > i:
                sim = compute_cosine_similarity(embeddings[genres[i]], embeddings[genres[j]])
                similarity_matrix[i, j] = sim
                similarity_matrix[j, i] = sim

            monitor_and_maybe_gc()

    return similarity_matrix

def calculate_mean_off_diagonal_similarity(similarity_matrix: np.ndarray) -> float:
    """
    Calculate mean of off-diagonal elements in similarity matrix.

    Args:
        similarity_matrix: Symmetric similarity matrix.

    Returns:
        Mean off-diagonal similarity.
    """
    n = similarity_matrix.shape[0]
    if n <= 1:
        return 0.0

    off_diagonal = similarity_matrix[~np.eye(n, dtype=bool)]
    return float(np.mean(off_diagonal))

def calculate_intra_genre_variance(embeddings: Dict[str, np.ndarray]) -> float:
    """
    Calculate variance within genre embeddings (placeholder for future implementation).

    Args:
        embeddings: Dictionary mapping genre names to embeddings.

    Returns:
        Variance measure.
    """
    # For now, return 0.0 as a placeholder
    # Future implementation would compute variance of embeddings within each genre
    return 0.0

def main() -> int:
    """Main entry point for similarity computation."""
    set_deterministic_seed(42)
    setup_logging("pipeline_log.txt")
    logger = get_logger()

    try:
        logger.info("Starting similarity computation...")

        # Load yearly embeddings
        embeddings_dir = Path("yearly_embeddings")
        if not embeddings_dir.exists():
            logger.error(f"Embeddings directory not found: {embeddings_dir}")
            return 1

        results = []

        for year_file in sorted(embeddings_dir.glob("*.npy")):
            year = int(year_file.stem)
            logger.info(f"Processing year {year}")

            try:
                year_embeddings = np.load(year_file, allow_pickle=True).item()
                if not year_embeddings:
                    logger.warning(f"No embeddings for year {year}")
                    continue

                # Compute similarity matrix
                sim_matrix = compute_pairwise_similarities(year_embeddings)

                # Calculate metrics
                mean_sim = calculate_mean_off_diagonal_similarity(sim_matrix)
                intra_var = calculate_intra_genre_variance(year_embeddings)

                results.append({
                    "year": year,
                    "mean_off_diagonal_similarity": mean_sim,
                    "intra_genre_variance": intra_var
                })

                monitor_and_maybe_gc()

            except Exception as e:
                logger.error(f"Error processing {year_file}: {str(e)}")
                continue

        # Save results
        output_path = Path("data/derived/yearly_similarity.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        import pandas as pd
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved similarity results to {output_path}")

        return 0

    except Exception as e:
        logger.error(f"Similarity computation failed: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
