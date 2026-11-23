"""
Similarity module for computing pairwise cosine similarities of yearly embeddings.
"""
import os
import gc
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import numpy as np
import pandas as pd

from utils import setup_logging, get_logger, set_deterministic_seed
from memory_utils import check_memory_thresholds, trigger_garbage_collection

logger = setup_logging()

YEARLY_EMBEDDINGS_DIR = Path(__file__).resolve().parent.parent / "yearly_embeddings"
DATA_DERIVED_DIR = Path(__file__).resolve().parent.parent / "data" / "derived"

def setup_logging_module():
    """
    Setup logging for the similarity module.
    """
    logger.info("Similarity module initialized.")

def load_yearly_embeddings() -> Dict[int, np.ndarray]:
    """
    Load yearly embeddings from the embeddings directory.

    Returns:
        Dict[int, np.ndarray]: Dictionary mapping years to embedding vectors.

    Raises:
        FileNotFoundError: If the embeddings directory is missing.
    """
    if not YEARLY_EMBEDDINGS_DIR.exists():
        raise FileNotFoundError(f"Embeddings directory not found: {YEARLY_EMBEDDINGS_DIR}")
    
    embeddings = {}
    for file in YEARLY_EMBEDDINGS_DIR.glob("*.npy"):
        year = int(file.stem)
        embeddings[year] = np.load(file)
    
    logger.info(f"Loaded embeddings for {len(embeddings)} years.")
    return embeddings

def compute_pairwise_cosine_similarity(vectors: Dict[int, np.ndarray]) -> Dict[Tuple[int, int], float]:
    """
    Compute pairwise cosine similarity between all yearly vectors.

    Args:
        vectors (Dict[int, np.ndarray]): Dictionary of year to vector.

    Returns:
        Dict[Tuple[int, int], float]: Dictionary of (year1, year2) to similarity.
    """
    similarities = {}
    years = sorted(vectors.keys())
    
    for i, year1 in enumerate(years):
        vec1 = vectors[year1]
        for year2 in years[i+1:]:
            vec2 = vectors[year2]
            # Cosine similarity
            sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            similarities[(year1, year2)] = sim
    
    return similarities

def calculate_mean_off_diagonal_similarity(similarities: Dict[Tuple[int, int], float]) -> float:
    """
    Calculate the mean off-diagonal similarity.

    Args:
        similarities (Dict[Tuple[int, int], float]): Pairwise similarities.

    Returns:
        float: Mean similarity.
    """
    if not similarities:
        return 0.0
    return np.mean(list(similarities.values()))

def calculate_intra_genre_variance(vectors: Dict[int, np.ndarray]) -> float:
    """
    Calculate the intra-genre variance (placeholder for now).

    Args:
        vectors (Dict[int, np.ndarray]): Dictionary of year to vector.

    Returns:
        float: Variance metric.
    """
    # Placeholder: In a real scenario, we'd compute variance within genres
    # For now, return variance of the vectors themselves
    all_vectors = np.array(list(vectors.values()))
    return np.var(all_vectors)

def process_year(year: int, vectors: Dict[int, np.ndarray]) -> Dict[str, Any]:
    """
    Process a single year's similarity metrics.

    Args:
        year (int): Year to process.
        vectors (Dict[int, np.ndarray]): Dictionary of year to vector.

    Returns:
        Dict[str, Any]: Metrics for the year.
    """
    # Placeholder: In a real scenario, we'd compute year-specific metrics
    return {
        'year': year,
        'mean_off_diagonal_similarity': calculate_mean_off_diagonal_similarity({}),
        'intra_genre_variance': calculate_intra_genre_variance(vectors)
    }

def main():
    """
    Main entry point for similarity computation.
    """
    set_deterministic_seed(42)
    setup_logging_module()
    
    try:
        # Load embeddings
        vectors = load_yearly_embeddings()
        
        # Compute similarities
        similarities = compute_pairwise_cosine_similarity(vectors)
        
        # Calculate metrics
        mean_sim = calculate_mean_off_diagonal_similarity(similarities)
        variance = calculate_intra_genre_variance(vectors)
        
        # Prepare results
        results = []
        years = sorted(vectors.keys())
        for i, year1 in enumerate(years):
            year_sims = [s for (y1, y2), s in similarities.items() if y1 == year1 or y2 == year1]
            mean_year_sim = np.mean(year_sims) if year_sims else 0.0
            results.append({
                'year': year1,
                'mean_off_diagonal_similarity': mean_year_sim,
                'intra_genre_variance': variance
            })
        
        # Save results
        df = pd.DataFrame(results)
        output_path = DATA_DERIVED_DIR / "yearly_similarity.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Saved similarity results to {output_path}")
        
        logger.info("Similarity calculation complete.")
        
    except Exception as e:
        logger.error(f"Similarity computation failed: {e}")
        raise

if __name__ == "__main__":
    main()
