"""
Task T022c: Mahalanobis Distance (Unconditional)

Computes the Mahalanobis distance for each sample in the cleaned dataset
using the global covariance matrix derived from teacher scores.
Handles singular matrices via pseudo-inverse.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# --- Project Relative Imports (API Surface) ---
# We import setup_logging, setup_directories, load_cleaned_data, etc.
# from the provided API surface in code/entanglement_scores.py or code/mahalanobis_distance.py stub.
# Since code/mahalanobis_distance.py is the file we are writing, we will define the helpers here
# or import from existing modules if they exist in the surface.
# The surface lists:
# code/mahalanobis_distance.py: setup_logging, setup_directories, load_model_selection, load_covariance_matrix,
#                               load_global_mean, load_cleaned_data, calculate_mahalanobis_distance, save_results, parse_args, main
# We will implement these functions here to satisfy the task.

def setup_logging(log_file: str = None) -> logging.Logger:
    logger = logging.getLogger("mahalanobis_distance")
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

def setup_directories(base_path: Path):
    """Ensure required directories exist."""
    dirs = [
        base_path / "data" / "processed",
        base_path / "results"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def load_cleaned_data(base_path: Path) -> pd.DataFrame:
    """Load data/processed/cleaned_data.parquet."""
    path = base_path / "data" / "processed" / "cleaned_data.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {path}")
    return pd.read_parquet(path)

def load_covariance_matrix(base_path: Path) -> np.ndarray:
    """Load results/covariance_matrix.json and convert to numpy array."""
    path = base_path / "results" / "covariance_matrix.json"
    if not path.exists():
        raise FileNotFoundError(f"Covariance matrix not found at {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Expected structure: {"matrix": [[...], ...], "dimensions": [...]}
    if "matrix" not in data:
        raise ValueError("Covariance matrix JSON missing 'matrix' key")
    
    return np.array(data["matrix"])

def load_global_mean(base_path: Path) -> np.ndarray:
    """
    Load global mean vector. 
    If results/global_mean.json doesn't exist, compute it from cleaned data.
    """
    path = base_path / "results" / "global_mean.json"
    
    if path.exists():
        with open(path, 'r') as f:
            data = json.load(f)
        return np.array(data["mean_vector"])
    
    # Fallback: compute from cleaned data if not explicitly saved
    # This assumes the covariance was computed on the same data
    df = load_cleaned_data(base_path)
    # Teacher scores are typically stored as a list or separate columns.
    # Based on T022a/T022b context, we need to extract the 4 teacher scores.
    # In the cleaned data, we expect columns like teacher_scores_0, teacher_scores_1, etc.
    # or a single column 'teacher_scores' containing lists.
    # Let's assume standard extraction logic used in T022b:
    if "teacher_scores" in df.columns:
        # If it's a list column
        scores_df = pd.DataFrame(df["teacher_scores"].tolist(), columns=["t0", "t1", "t2", "t3"])
        return scores_df.mean().values
    else:
        # Try column names
        cols = [c for c in df.columns if c.startswith("teacher_score_")]
        if len(cols) == 4:
            return df[cols].mean().values
        else:
            raise ValueError("Could not determine teacher score columns for mean calculation")

def calculate_mahalanobis_distance(
    df: pd.DataFrame, 
    cov_matrix: np.ndarray, 
    mean_vector: np.ndarray
) -> np.ndarray:
    """
    Calculate Mahalanobis distance for each sample.
    Handles singular matrices using numpy.linalg.pinv.
    """
    # Extract teacher scores from DataFrame
    # Assumption: 'teacher_scores' column contains lists/arrays of length 4
    if "teacher_scores" not in df.columns:
        raise ValueError("DataFrame missing 'teacher_scores' column")
    
    # Convert list column to numpy array
    scores_array = np.array(df["teacher_scores"].tolist())
    
    # Check dimensions
    if scores_array.shape[1] != cov_matrix.shape[0]:
        raise ValueError(f"Dimension mismatch: scores {scores_array.shape[1]} vs cov {cov_matrix.shape[0]}")
    
    # Center the data
    diff = scores_array - mean_vector
    
    # Compute inverse (or pseudo-inverse) of covariance matrix
    # Using pinv with rcond=1e-15 as per task requirements
    try:
        cov_inv = np.linalg.pinv(cov_matrix, rcond=1e-15)
    except np.linalg.LinAlgError as e:
        raise RuntimeError(f"Failed to compute pseudo-inverse of covariance matrix: {e}")
    
    # Mahalanobis distance: sqrt( (x - mu) @ inv(C) @ (x - mu).T )
    # For each row:
    # m_dist = sqrt( sum_i ( (x_i - mu) * inv(C) ) * (x_i - mu) )
    # Vectorized:
    left = np.dot(diff, cov_inv)
    mahal_sq = np.sum(left * diff, axis=1)
    
    # Ensure non-negative (numerical errors might cause tiny negatives)
    mahal_sq = np.maximum(mahal_sq, 0.0)
    mahal_dist = np.sqrt(mahal_sq)
    
    return mahal_dist

def save_results(
    df: pd.DataFrame, 
    distances: np.ndarray, 
    base_path: Path
):
    """
    Merge distances into features.json (data/processed/features.json).
    The task says: 'merge as mahalanobis_distance into data/processed/features.json'.
    """
    df["mahalanobis_distance"] = distances
    
    output_path = base_path / "data" / "processed" / "features.json"
    
    # Convert to JSON serializable format
    # If features.json is expected to be a list of dicts
    records = df.to_dict(orient='records')
    
    with open(output_path, 'w') as f:
        json.dump(records, f, indent=2)
    
    logging.info(f"Saved updated features to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Compute Mahalanobis Distance for T022c")
    parser.add_argument("--base-path", type=str, default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala",
                        help="Base path of the project")
    return parser.parse_args()

def main():
    args = parse_args()
    base_path = Path(args.base_path)
    
    # Setup
    logger = setup_logging(base_path / "data" / "processed" / "mahalanobis_distance.log")
    setup_directories(base_path)
    
    logger.info("Loading cleaned data...")
    df = load_cleaned_data(base_path)
    logger.info(f"Loaded {len(df)} samples.")
    
    logger.info("Loading covariance matrix...")
    cov_matrix = load_covariance_matrix(base_path)
    logger.info(f"Covariance matrix shape: {cov_matrix.shape}")
    
    logger.info("Loading global mean...")
    mean_vector = load_global_mean(base_path)
    logger.info(f"Mean vector shape: {mean_vector.shape}")
    
    logger.info("Computing Mahalanobis distances...")
    distances = calculate_mahalanobis_distance(df, cov_matrix, mean_vector)
    logger.info(f"Computed distances. Range: [{distances.min():.4f}, {distances.max():.4f}]")
    
    logger.info("Saving results to features.json...")
    save_results(df, distances, base_path)
    
    logger.info("Task T022c completed successfully.")

if __name__ == "__main__":
    main()