"""
Feature Engineering Module for llmXive Follow-up Project.

This module provides statistical helper functions for calculating entanglement
metrics (variance, entropy, skewness, kurtosis) and global covariance properties
from teacher score distributions.
"""

import argparse
import json
import logging
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Project root relative to this file (assuming code/ is the root for imports)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure and return the project logger."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger("features")

def setup_directories() -> Tuple[Path, Path]:
    """Ensure output directories exist."""
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_PROCESSED_DIR, RESULTS_DIR

def load_raw_dataset(path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the raw dataset from Parquet.

    Args:
        path: Path to the raw dataset. Defaults to data/processed/raw_data.parquet.

    Returns:
        Loaded pandas DataFrame.
    """
    if path is None:
        path = str(DATA_PROCESSED_DIR / "raw_data.parquet")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raw dataset not found at {path}")
    
    logger = logging.getLogger("features")
    logger.info(f"Loading raw dataset from {path}")
    return pd.read_parquet(path)

def load_cleaned_dataset(path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the cleaned dataset from Parquet.

    Args:
        path: Path to the cleaned dataset. Defaults to data/processed/cleaned_data.parquet.

    Returns:
        Loaded pandas DataFrame.
    """
    if path is None:
        path = str(DATA_PROCESSED_DIR / "cleaned_data.parquet")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Cleaned dataset not found at {path}")
    
    logger = logging.getLogger("features")
    logger.info(f"Loading cleaned dataset from {path}")
    return pd.read_parquet(path)

def extract_teacher_scores_matrix(df: pd.DataFrame) -> np.ndarray:
    """
    Extract the N x 4 matrix of teacher scores for the four rubric dimensions.

    Expected columns: 'Alignment', 'Realism', 'Aesthetics', 'Plausibility'.
    
    Args:
        df: DataFrame containing teacher scores.

    Returns:
        Numpy array of shape (N, 4).
    """
    dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    
    # Check if the data is in a nested structure or flat
    if "teacher_scores" in df.columns:
        # If it's a column of dicts/objects, expand it
        if isinstance(df["teacher_scores"].iloc[0], dict):
            scores_df = pd.DataFrame(df["teacher_scores"].tolist(), index=df.index)
            # Ensure order
            scores_matrix = scores_df[dimensions].values
        else:
            raise ValueError("teacher_scores column contains non-dict objects")
    else:
        # Assume flat columns exist
        if not all(dim in df.columns for dim in dimensions):
            raise ValueError(f"Missing teacher score dimensions. Expected: {dimensions}")
        scores_matrix = df[dimensions].values

    return scores_matrix.astype(float)

def calculate_variance_and_range(scores: np.ndarray) -> Tuple[float, float]:
    """
    Calculate variance and range for a 1D array of scores.

    Args:
        scores: 1D numpy array of scores.

    Returns:
        Tuple of (variance, range).
    """
    if len(scores) == 0:
        return 0.0, 0.0
    
    variance = np.var(scores)
    range_val = float(np.max(scores) - np.min(scores)) if len(scores) > 1 else 0.0
    return variance, range_val

def calculate_entropy(scores: np.ndarray) -> float:
    """
    Calculate Shannon entropy for a 1D array of scores.
    Uses histogram binning for continuous data.

    Args:
        scores: 1D numpy array of scores.

    Returns:
        Entropy value (float). Returns 0.0 for zero variance.
    """
    if len(scores) <= 1:
        return 0.0
    
    variance = np.var(scores)
    if variance < 1e-10:
        return 0.0

    # Use histogram to estimate probability distribution
    # Using 10 bins as a standard heuristic for small dimensions
    counts, _ = np.histogram(scores, bins=10)
    
    # Filter out zero counts to avoid log(0)
    probs = counts[counts > 0] / len(scores)
    
    if len(probs) == 0:
        return 0.0
    
    entropy = -np.sum(probs * np.log(probs))
    return float(entropy)

def calculate_skewness_and_kurtosis(scores: np.ndarray) -> Tuple[float, float]:
    """
    Calculate skewness and kurtosis for a 1D array of scores.

    Args:
        scores: 1D numpy array of scores.

    Returns:
        Tuple of (skewness, kurtosis).
    """
    if len(scores) < 3:
        return 0.0, 0.0
    
    skew = float(stats.skew(scores))
    kurt = float(stats.kurtosis(scores)) # Fisher's definition (normal=0)
    return skew, kurt

def calculate_global_covariance_and_eigenvalue(scores_matrix: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Calculate the global covariance matrix and its dominant eigenvalue.

    Args:
        scores_matrix: N x 4 numpy array of teacher scores.

    Returns:
        Tuple of (covariance_matrix, dominant_eigenvalue).
    """
    if scores_matrix.shape[0] < 2:
        raise ValueError("Need at least 2 samples to compute covariance.")
    
    # Compute covariance matrix (rowvar=False means columns are variables)
    cov_matrix = np.cov(scores_matrix, rowvar=False)
    
    # Compute eigenvalues
    eigenvalues, _ = np.linalg.eig(cov_matrix)
    
    # Filter for real eigenvalues (should be real for symmetric matrix)
    real_eigenvalues = np.real(eigenvalues)
    
    if len(real_eigenvalues) == 0:
        raise ValueError("No real eigenvalues found.")
    
    dominant_eigenvalue = float(np.max(real_eigenvalues))
    
    return cov_matrix, dominant_eigenvalue

def compute_per_sample_stats(scores_matrix: np.ndarray) -> List[Dict[str, float]]:
    """
    Compute per-sample statistical features: variance, entropy, skewness, kurtosis.
    Note: Mahalanobis distance is computed separately using global covariance.

    Args:
        scores_matrix: N x 4 numpy array.

    Returns:
        List of dictionaries, one per sample.
    """
    n_samples = scores_matrix.shape[0]
    features = []
    
    for i in range(n_samples):
        sample_scores = scores_matrix[i]
        
        var, rng = calculate_variance_and_range(sample_scores)
        ent = calculate_entropy(sample_scores)
        skew, kurt = calculate_skewness_and_kurtosis(sample_scores)
        
        features.append({
            "variance": var,
            "entropy": ent,
            "skewness": skew,
            "kurtosis": kurt
        })
    
    return features

def calculate_mahalanobis_distance(
    scores_matrix: np.ndarray, 
    mean_vector: np.ndarray, 
    cov_matrix: np.ndarray
) -> np.ndarray:
    """
    Calculate Mahalanobis distance for each sample.

    Args:
        scores_matrix: N x 4 numpy array.
        mean_vector: 1D array of shape (4,).
        cov_matrix: 4 x 4 covariance matrix.

    Returns:
        1D array of distances.
    """
    # Use pseudo-inverse for singular matrices
    try:
        cov_inv = np.linalg.inv(cov_matrix)
    except np.linalg.LinAlgError:
        logging.warning("Covariance matrix is singular, using pseudo-inverse.")
        cov_inv = np.linalg.pinv(cov_matrix, rcond=1e-15)
    
    diff = scores_matrix - mean_vector
    # (x - mu)^T * Sigma^-1 * (x - mu)
    # For vectorized: sum over axis 1 of (diff @ cov_inv) * diff
    mahal_sq = np.sum(diff @ cov_inv * diff, axis=1)
    
    # Ensure non-negative due to floating point errors
    mahal_sq = np.maximum(mahal_sq, 0)
    return np.sqrt(mahal_sq)

def integrate_features(
    df: pd.DataFrame, 
    per_sample_stats: List[Dict[str, float]], 
    mahalanobis_distances: np.ndarray,
    dominant_eigenvalue: Optional[float] = None
) -> pd.DataFrame:
    """
    Integrate calculated features back into the DataFrame.

    Args:
        df: Original DataFrame.
        per_sample_stats: List of dicts with variance, entropy, etc.
        mahalanobis_distances: Array of Mahalanobis distances.
        dominant_eigenvalue: Optional global eigenvalue to log (not stored per sample).

    Returns:
        DataFrame with new feature columns.
    """
    df_out = df.copy()
    
    # Convert stats list to DataFrame
    stats_df = pd.DataFrame(per_sample_stats)
    
    # Concatenate
    df_out = pd.concat([df_out, stats_df], axis=1)
    
    # Add Mahalanobis distance
    df_out["mahalanobis_distance"] = mahalanobis_distances
    
    # Log global eigenvalue if provided (metadata only, not stored in row)
    if dominant_eigenvalue is not None:
        logging.info(f"Global Dominant Eigenvalue: {dominant_eigenvalue}")
    
    return df_out

def save_global_stats(cov_matrix: np.ndarray, eigenvalue: float, results_dir: Path) -> None:
    """
    Save global covariance matrix and eigenvalue to JSON.

    Args:
        cov_matrix: 4x4 numpy array.
        eigenvalue: Float dominant eigenvalue.
        results_dir: Path to results directory.
    """
    cov_path = results_dir / "covariance_matrix.json"
    eigen_path = results_dir / "dominant_eigenvalue.json"
    
    with open(cov_path, "w") as f:
        json.dump(cov_matrix.tolist(), f, indent=2)
    
    with open(eigen_path, "w") as f:
        json.dump({"dominant_eigenvalue": eigenvalue}, f, indent=2)
    
    logging.info(f"Saved covariance matrix to {cov_path}")
    logging.info(f"Saved dominant eigenvalue to {eigen_path}")

def save_features_to_csv(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save features DataFrame to CSV (or JSON if preferred, but CSV is standard for tabular).
    The task spec mentions features.json, so we will also support JSON if needed.
    Here we save to the specific path requested in tasks.md: data/processed/features.json
    
    Args:
        df: DataFrame with features.
        output_path: Path to output file.
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to list of dicts for JSON serialization
    records = df.to_dict(orient="records")
    
    with open(output_path, "w") as f:
        json.dump(records, f, indent=2)
    
    logging.info(f"Saved features to {output_path}")

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Feature Engineering for llmXive")
    parser.add_argument(
        "--input-raw", 
        type=str, 
        default=None,
        help="Path to raw dataset (default: data/processed/raw_data.parquet)"
    )
    parser.add_argument(
        "--input-cleaned", 
        type=str, 
        default=None,
        help="Path to cleaned dataset (default: data/processed/cleaned_data.parquet)"
    )
    parser.add_argument(
        "--output-features", 
        type=str, 
        default=None,
        help="Path to output features file (default: data/processed/features.json)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable debug logging"
    )
    return parser.parse_args()

def main() -> int:
    """Main entry point for feature engineering."""
    args = parse_args()
    logger = setup_logging(args.verbose)
    
    try:
        data_dir, results_dir = setup_directories()
        
        # Determine input source: prefer cleaned data for per-sample stats if available,
        # otherwise raw. T022a/T022c depend on T024 (cleaned).
        input_path = args.input_cleaned
        if not input_path:
            input_path = str(data_dir / "cleaned_data.parquet")
        
        if not os.path.exists(input_path):
            # Fallback to raw if cleaned doesn't exist yet (for T022b-raw context)
            input_path = args.input_raw or str(data_dir / "raw_data.parquet")
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Neither cleaned nor raw dataset found at expected paths.")
            logger.warning(f"Using raw dataset from {input_path}")
        
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded dataset with {len(df)} samples")
        
        # Extract teacher scores
        scores_matrix = extract_teacher_scores_matrix(df)
        logger.info(f"Extracted teacher scores matrix: {scores_matrix.shape}")
        
        # Compute global stats (needed for Mahalanobis and eigenvalue)
        cov_matrix, dominant_eigenvalue = calculate_global_covariance_and_eigenvalue(scores_matrix)
        logger.info(f"Global Covariance computed. Dominant Eigenvalue: {dominant_eigenvalue}")
        
        # Save global stats
        save_global_stats(cov_matrix, dominant_eigenvalue, results_dir)
        
        # Compute per-sample stats
        per_sample_stats = compute_per_sample_stats(scores_matrix)
        
        # Compute mean vector for Mahalanobis
        mean_vector = np.mean(scores_matrix, axis=0)
        
        # Compute Mahalanobis distance
        mahal_distances = calculate_mahalanobis_distance(scores_matrix, mean_vector, cov_matrix)
        
        # Integrate features
        df_features = integrate_features(df, per_sample_stats, mahal_distances, dominant_eigenvalue)
        
        # Determine output path
        output_path = args.output_features
        if not output_path:
            output_path = str(data_dir / "features.json")
        
        save_features_to_csv(df_features, Path(output_path))
        
        logger.info("Feature engineering completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Feature engineering failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())