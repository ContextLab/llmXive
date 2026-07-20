import os
import gc
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import numpy as np
import pandas as pd

# Import shared utilities from the project root
from utils import setup_logging, get_logger, set_deterministic_seed
from memory_utils import check_memory_checkpoint, trigger_garbage_collection

# Constants
EMBEDDINGS_DIR = Path("data/derived/yearly_embeddings")
OUTPUT_CSV = Path("data/derived/yearly_similarity.csv")
LOG_FILE = Path("pipeline_log.txt")
LOW_COVERAGE_FILE = Path("data/derived/low_coverage_years.json")
SEED = 42

def setup_logging_module():
    """Configure logging for the similarity module."""
    setup_logging(log_file=LOG_FILE)
    return get_logger(__name__)

def load_yearly_embeddings(year: int, logger: logging.Logger) -> Optional[Tuple[np.ndarray, List[str]]]:
    """
    Load the genre embedding matrix and corresponding genre labels for a specific year.
    
    Args:
        year: The calendar year to load.
        logger: The logger instance.
        
    Returns:
        Tuple of (embedding_matrix, genre_labels) or None if file missing.
    """
    emb_path = EMBEDDINGS_DIR / f"{year}.npy"
    meta_path = EMBEDDINGS_DIR / f"{year}_meta.json"
    
    if not emb_path.exists():
        logger.warning(f"Embedding file missing for year {year}: {emb_path}")
        return None
    
    try:
        logger.info(f"Loading embeddings for {year} from {emb_path}")
        embeddings = np.load(emb_path, mmap_mode='r')
        
        if meta_path.exists():
            with open(meta_path, 'r') as f:
                meta = json.load(f)
            labels = meta.get('genres', [])
        else:
            # Fallback if meta missing: assume indices map to 0..N-1
            labels = [str(i) for i in range(embeddings.shape[0])]
        
        logger.info(f"Loaded {embeddings.shape[0]} genres for {year} (dim={embeddings.shape[1]})")
        return embeddings, labels
    except Exception as e:
        logger.error(f"Failed to load embeddings for {year}: {e}")
        return None

def compute_pairwise_cosine_similarity(embeddings: np.ndarray) -> np.ndarray:
    """
    Compute the pairwise cosine similarity matrix for a set of vectors.
    
    Args:
        embeddings: N x D matrix of vectors.
        
    Returns:
        N x N similarity matrix.
    """
    # Normalize vectors to unit length
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    # Avoid division by zero for zero vectors
    norms = np.where(norms == 0, 1, norms)
    normalized = embeddings / norms
    
    # Cosine similarity is dot product of normalized vectors
    similarity_matrix = np.dot(normalized, normalized.T)
    
    # Clip to [-1, 1] to handle floating point errors
    return np.clip(similarity_matrix, -1.0, 1.0)

def calculate_mean_off_diagonal_similarity(similarity_matrix: np.ndarray) -> float:
    """
    Calculate the mean similarity of all off-diagonal elements.
    
    Args:
        similarity_matrix: N x N similarity matrix.
        
    Returns:
        Mean off-diagonal similarity.
    """
    n = similarity_matrix.shape[0]
    if n <= 1:
        return 0.0
    
    # Create a mask for off-diagonal elements
    mask = ~np.eye(n, dtype=bool)
    off_diagonal_values = similarity_matrix[mask]
    
    if len(off_diagonal_values) == 0:
        return 0.0
        
    return float(np.mean(off_diagonal_values))

def calculate_intra_genre_variance(similarity_matrix: np.ndarray) -> float:
    """
    Calculate the variance of the diagonal elements (self-similarity).
    Ideally should be 1.0, but variance captures numerical drift or normalization issues.
    
    Args:
        similarity_matrix: N x N similarity matrix.
        
    Returns:
        Variance of diagonal elements.
    """
    diag = np.diag(similarity_matrix)
    return float(np.var(diag))

def process_year(year: int, logger: logging.Logger) -> Optional[Dict]:
    """
    Process a single year: load embeddings, compute similarities, and return metrics.
    
    Args:
        year: The year to process.
        logger: The logger instance.
        
    Returns:
        Dictionary with metrics or None if processing failed.
    """
    data = load_yearly_embeddings(year, logger)
    if data is None:
        return None
        
    embeddings, labels = data
    
    # Check memory before heavy computation
    check_memory_checkpoint(logger, threshold_gb=5.0)
    
    # Compute similarity matrix
    logger.info(f"Computing pairwise similarity for {year}...")
    sim_matrix = compute_pairwise_cosine_similarity(embeddings)
    
    # Calculate metrics
    mean_off_diag = calculate_mean_off_diagonal_similarity(sim_matrix)
    intra_var = calculate_intra_genre_variance(sim_matrix)
    
    logger.info(f"Year {year}: Mean Off-Diagonal={mean_off_diag:.4f}, Intra-Var={intra_var:.4f}")
    
    # Cleanup
    del embeddings, sim_matrix
    gc.collect()
    
    return {
        "year": year,
        "mean_off_diagonal_similarity": mean_off_diag,
        "intra_genre_variance": intra_var,
        "num_genres": len(labels)
    }

def main():
    """Main entry point for similarity calculation."""
    logger = setup_logging_module()
    set_deterministic_seed(SEED)
    
    logger.info("Starting similarity calculation pipeline...")
    
    if not EMBEDDINGS_DIR.exists():
        logger.error(f"Embeddings directory not found: {EMBEDDINGS_DIR}")
        raise FileNotFoundError(f"Embeddings directory not found: {EMBEDDINGS_DIR}")
    
    # Discover available years
    year_files = list(EMBEDDINGS_DIR.glob("*.npy"))
    if not year_files:
        logger.error("No embedding files found in yearly_embeddings directory.")
        raise FileNotFoundError("No embedding files found.")
    
    years = sorted([int(f.stem) for f in year_files])
    logger.info(f"Discovered years: {years}")
    
    results = []
    failed_years = []
    
    for year in years:
        try:
            res = process_year(year, logger)
            if res:
                results.append(res)
            else:
                failed_years.append(year)
        except Exception as e:
            logger.error(f"Critical error processing year {year}: {e}")
            failed_years.append(year)
    
    if failed_years:
        logger.warning(f"Failed to process years: {failed_years}")
    
    if not results:
        logger.error("No successful results generated. Aborting.")
        raise RuntimeError("No similarity results generated.")
    
    # Save results to CSV
    df = pd.DataFrame(results)
    df = df.sort_values("year")
    
    logger.info(f"Saving results to {OUTPUT_CSV}")
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    
    logger.info("Similarity calculation complete")
    logger.info(f"Output saved to: {OUTPUT_CSV.resolve()}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Years processed: {len(results)}")
    print(f"  Years failed: {len(failed_years)}")
    print(f"  Avg Mean Off-Diagonal: {df['mean_off_diagonal_similarity'].mean():.4f}")
    
    return 0

if __name__ == "__main__":
    exit(main())