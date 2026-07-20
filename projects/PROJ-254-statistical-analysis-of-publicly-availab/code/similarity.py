"""
Similarity module for computing pairwise cosine similarities and generating visual artifacts.
"""
import os
import gc
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

from utils import setup_logging, get_logger, set_deterministic_seed

logger = setup_logging()

DATA_DERIVED_DIR = Path(__file__).resolve().parent.parent / "data" / "derived"
YEARLY_EMBEDDINGS_DIR = DATA_DERIVED_DIR.parent / "yearly_embeddings"

def setup_logging_module():
    """
    Setup logging for similarity module.
    """
    logger.info("Similarity module logging setup complete.")

def load_yearly_embeddings() -> Dict[int, np.ndarray]:
    """
    Load yearly embeddings from npy files.
    """
    embeddings = {}
    for file in YEARLY_EMBEDDINGS_DIR.glob("*.npy"):
        year = int(file.stem)
        vec = np.load(file)
        embeddings[year] = vec
    return embeddings

def compute_pairwise_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return np.dot(vec1, vec2) / (norm1 * norm2)

def calculate_mean_off_diagonal_similarity(similarity_matrix: np.ndarray) -> float:
    """
    Calculate mean off-diagonal similarity.
    """
    n = similarity_matrix.shape[0]
    if n <= 1:
        return 0.0
    # Mask diagonal
    mask = ~np.eye(n, dtype=bool)
    return np.mean(similarity_matrix[mask])

def calculate_intra_genre_variance(similarity_matrix: np.ndarray) -> float:
    """
    Calculate intra-genre variance.
    """
    return np.var(similarity_matrix)

def process_year(year: int, embeddings: Dict[int, np.ndarray]) -> Tuple[int, float, float]:
    """
    Process a specific year's similarity.
    """
    # For this demo, we assume we compare the year's vector against all others
    # Or compute similarity matrix if we had multiple vectors per year.
    # Since we have one vector per year, we compute similarity to neighbors?
    # The spec implies pairwise similarity between yearly genre vectors.
    # We will compute similarity between the current year and all other years.
    
    current_vec = embeddings.get(year)
    if current_vec is None:
        return year, 0.0, 0.0
    
    similarities = []
    for other_year, other_vec in embeddings.items():
        if other_year == year:
            continue
        sim = compute_pairwise_cosine_similarity(current_vec, other_vec)
        similarities.append(sim)
    
    if not similarities:
        return year, 0.0, 0.0
    
    mean_sim = np.mean(similarities)
    var_sim = np.var(similarities)
    
    return year, mean_sim, var_sim

def main():
    """
    Main entry point for similarity calculation.
    """
    set_deterministic_seed(42)
    setup_logging_module()
    
    try:
        embeddings = load_yearly_embeddings()
        logger.info(f"Loaded {len(embeddings)} yearly embeddings.")
        
        results = []
        for year in sorted(embeddings.keys()):
            year, mean_sim, var_sim = process_year(year, embeddings)
            results.append({
                "year": year,
                "mean_off_diagonal_similarity": mean_sim,
                "intra_genre_variance": var_sim
            })
        
        df = pd.DataFrame(results)
        output_path = DATA_DERIVED_DIR / "yearly_similarity.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Saved similarity results to {output_path}")
        
        logger.info("Similarity calculation complete.")
        
    except Exception as e:
        logger.error(f"Similarity calculation failed: {e}")
        raise

if __name__ == "__main__":
    main()
