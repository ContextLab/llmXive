"""
Feature engineering module for llmXive pipeline.
Implements statistical helper functions for teacher score entanglement analysis.
"""

import argparse
import json
import logging
import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats

# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure and return the project logger."""
    logger = logging.getLogger("llmXive.features")
    logger.setLevel(log_level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# ============================================================================
# Directory Setup
# ============================================================================

def setup_directories(base_path: Path) -> Tuple[Path, Path, Path]:
    """
    Ensure required directories exist.
    Returns: (raw_dir, processed_dir, results_dir)
    """
    raw_dir = base_path / "data" / "raw"
    processed_dir = base_path / "data" / "processed"
    results_dir = base_path / "results"

    for d in [raw_dir, processed_dir, results_dir]:
        d.mkdir(parents=True, exist_ok=True)

    return raw_dir, processed_dir, results_dir

# ============================================================================
# Data Loading
# ============================================================================

def load_raw_dataset(raw_dir: Path, filename: str = "z_reward.parquet") -> pd.DataFrame:
    """
    Load the raw dataset from disk.
    Raises FileNotFoundError if the file does not exist.
    """
    file_path = raw_dir / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {file_path}")

    logger = logging.getLogger("llmXive.features")
    logger.info(f"Loading raw dataset from {file_path}")

    try:
        df = pd.read_parquet(file_path)
        logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
        return df
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        raise

# ============================================================================
# Data Extraction
# ============================================================================

def extract_teacher_scores_matrix(df: pd.DataFrame) -> np.ndarray:
    """
    Extract the 4-dimensional teacher score vector for each sample.
    Expected columns inside 'teacher_scores' object: Alignment, Realism, Aesthetics, Plausibility.
    Returns: N x 4 numpy array.
    """
    logger = logging.getLogger("llmXive.features")

    if "teacher_scores" not in df.columns:
        raise ValueError("Column 'teacher_scores' not found in dataset.")

    # Normalize: ensure 'teacher_scores' is a list of dicts or a Series of dicts
    # If it's a Series of dicts, we expand it.
    if isinstance(df["teacher_scores"].iloc[0], dict):
        scores_df = pd.DataFrame(df["teacher_scores"].tolist(), index=df.index)
    else:
        # Attempt to parse JSON strings if stored as such
        try:
            scores_df = pd.DataFrame(
                df["teacher_scores"].apply(lambda x: json.loads(x) if isinstance(x, str) else x).tolist(),
                index=df.index
            )
        except Exception as e:
            logger.error(f"Failed to parse teacher_scores column: {e}")
            raise

    required_dims = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    missing = [d for d in required_dims if d not in scores_df.columns]
    if missing:
        raise ValueError(f"Missing required teacher score dimensions: {missing}")

    matrix = scores_df[required_dims].to_numpy(dtype=float)

    # Handle NaN/Inf
    if np.any(~np.isfinite(matrix)):
        logger.warning("Non-finite values found in teacher scores. Replacing with 0.0.")
        matrix = np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0)

    return matrix

# ============================================================================
# Statistical Helper Functions
# ============================================================================

def calculate_variance_and_range(values: np.ndarray) -> Tuple[float, float]:
    """
    Calculate variance and range for a 1D array of values.
    Handles zero-variance cases gracefully.
    """
    if values.size == 0:
        return 0.0, 0.0

    var_val = np.var(values)
    range_val = np.ptp(values)  # peak-to-peak (max - min)

    return float(var_val), float(range_val)

def calculate_entropy(values: np.ndarray) -> float:
    """
    Calculate Shannon entropy for a distribution.
    Normalizes values to sum to 1.0 before calculation.
    Handles zero-variance or zero-sum cases.
    """
    if values.size == 0:
        return 0.0

    # Normalize to probability distribution
    p = values.astype(float)
    p_sum = np.sum(p)
    if p_sum == 0:
        return 0.0

    p = p / p_sum

    # Filter out zeros to avoid log(0)
    p_nonzero = p[p > 0]

    if len(p_nonzero) == 0:
        return 0.0

    entropy_val = -np.sum(p_nonzero * np.log(p_nonzero))
    return float(entropy_val)

def calculate_skewness_and_kurtosis(values: np.ndarray) -> Tuple[float, float]:
    """
    Calculate skewness and kurtosis for a 1D array.
    Uses scipy.stats for robust calculation.
    """
    if values.size < 2:
        return 0.0, 0.0

    try:
        skew_val = stats.skew(values, nan_policy='omit')
        kurt_val = stats.kurtosis(values, nan_policy='omit')
    except Exception:
        return 0.0, 0.0

    # Handle NaN results (e.g., constant array)
    if not np.isfinite(skew_val):
        skew_val = 0.0
    if not np.isfinite(kurt_val):
        kurt_val = 0.0

    return float(skew_val), float(kurt_val)

def compute_per_sample_stats(matrix: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Compute per-sample statistics across the 4 dimensions.
    Args:
        matrix: N x 4 numpy array of teacher scores.
    Returns:
        Dict with keys: 'variance', 'entropy', 'skewness', 'kurtosis'.
        Values are N-length arrays.
    """
    n_samples = matrix.shape[0]
    logger = logging.getLogger("llmXive.features")
    logger.info(f"Computing per-sample stats for {n_samples} samples.")

    variances = np.zeros(n_samples)
    entropies = np.zeros(n_samples)
    skewnesses = np.zeros(n_samples)
    kurtoses = np.zeros(n_samples)

    for i in range(n_samples):
        row = matrix[i]
        variances[i], _ = calculate_variance_and_range(row)
        entropies[i] = calculate_entropy(row)
        skewnesses[i], kurtoses[i] = calculate_skewness_and_kurtosis(row)

    return {
        "variance": variances,
        "entropy": entropies,
        "skewness": skewnesses,
        "kurtosis": kurtoses
    }

def calculate_global_covariance_and_eigenvalue(matrix: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Calculate the global covariance matrix and its dominant eigenvalue.
    Args:
        matrix: N x 4 numpy array.
    Returns:
        Tuple of (covariance_matrix, dominant_eigenvalue).
    """
    logger = logging.getLogger("llmXive.features")
    logger.info("Calculating global covariance matrix.")

    if matrix.shape[0] < 2:
        logger.warning("Insufficient samples for covariance calculation. Returning identity.")
        cov_matrix = np.eye(4)
        return cov_matrix, 1.0

    # rowvar=False means columns are variables (dimensions), rows are observations (samples)
    cov_matrix = np.cov(matrix, rowvar=False)

    # Ensure symmetric
    cov_matrix = (cov_matrix + cov_matrix.T) / 2

    # Calculate eigenvalues
    try:
        eigenvalues, _ = np.linalg.eigh(cov_matrix)
    except np.linalg.LinAlgError:
        logger.error("Failed to compute eigenvalues. Using pseudo-inverse approach.")
        # Fallback: use pinv to get eigenvalues? No, eigh is standard.
        # If it fails, return zero matrix
        eigenvalues = np.zeros(4)

    dominant_eigenvalue = float(np.max(eigenvalues))
    logger.info(f"Dominant eigenvalue: {dominant_eigenvalue}")

    return cov_matrix, dominant_eigenvalue

# ============================================================================
# Integration & Output
# ============================================================================

def save_global_stats(
    processed_dir: Path,
    cov_matrix: np.ndarray,
    dominant_eigenvalue: float
) -> None:
    """Save global covariance matrix and dominant eigenvalue to JSON."""
    cov_path = processed_dir / "global_covariance_matrix.json"
    eigen_path = processed_dir / "dominant_eigenvalue.json"

    # Save covariance matrix
    with open(cov_path, "w") as f:
        json.dump(cov_matrix.tolist(), f, indent=2)
    logging.getLogger("llmXive.features").info(f"Saved covariance matrix to {cov_path}")

    # Save dominant eigenvalue
    with open(eigen_path, "w") as f:
        json.dump({"dominant_eigenvalue": dominant_eigenvalue}, f, indent=2)
    logging.getLogger("llmXive.features").info(f"Saved dominant eigenvalue to {eigen_path}")

# ============================================================================
# Argument Parsing & Main Entry
# ============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute statistical features for teacher score entanglement analysis."
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala",
        help="Base path of the project."
    )
    parser.add_argument(
        "--input-file",
        type=str,
        default="z_reward.parquet",
        help="Name of the raw dataset file in data/raw/."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level."
    )
    return parser.parse_args()

def main() -> None:
    """Main entry point for feature engineering."""
    args = parse_args()
    logger = setup_logging(getattr(logging, args.log_level))
    base_path = Path(args.base_path)

    # Setup directories
    raw_dir, processed_dir, _ = setup_directories(base_path)

    try:
        # Load data
        df = load_raw_dataset(raw_dir, args.input_file)

        # Extract teacher scores
        teacher_matrix = extract_teacher_scores_matrix(df)

        # Compute per-sample stats
        per_sample_stats = compute_per_sample_stats(teacher_matrix)

        # Compute global stats
        cov_matrix, dominant_eig = calculate_global_covariance_and_eigenvalue(teacher_matrix)

        # Save global stats
        save_global_stats(processed_dir, cov_matrix, dominant_eig)

        # Integrate per-sample stats into dataframe
        for key, values in per_sample_stats.items():
            df[key] = values

        # Output features to JSON (for downstream tasks)
        features_path = processed_dir / "features_base.json"
        features_list = df.to_dict(orient="records")
        with open(features_path, "w") as f:
            json.dump(features_list, f, indent=2)

        logger.info(f"Successfully processed {len(df)} samples. Features saved to {features_path}")

    except FileNotFoundError as e:
        logger.error(f"Data loading error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()