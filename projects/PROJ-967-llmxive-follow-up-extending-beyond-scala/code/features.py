"""
Feature Engineering Module for llmXive Follow-up Project.

This module provides statistical helper functions and the main pipeline
for calculating entanglement features (variance, entropy, skewness, kurtosis)
and global covariance metrics from teacher score distributions.

It extends the existing skeleton to implement the actual statistical logic
required for US2 (Entanglement Quantification).
"""

import argparse
import json
import logging
import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd

# --- Logging Setup ---

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure and return the project logger."""
    logger = logging.getLogger("llmxive_features")
    logger.setLevel(log_level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logger.addHandler(handler)
    return logger

logger = setup_logging()

# --- Directory Setup ---

def setup_directories(base_path: Optional[Path] = None) -> Tuple[Path, Path, Path]:
    """
    Ensure required directories exist.
    Returns: (raw_dir, processed_dir, results_dir)
    """
    if base_path is None:
        # Default to project root relative to this file's location
        base_path = Path(__file__).resolve().parent.parent

    raw_dir = base_path / "data" / "raw"
    processed_dir = base_path / "data" / "processed"
    results_dir = base_path / "results"

    for d in [raw_dir, processed_dir, results_dir]:
        d.mkdir(parents=True, exist_ok=True)

    return raw_dir, processed_dir, results_dir

# --- Data Loading ---

def load_raw_dataset(file_path: str) -> pd.DataFrame:
    """
    Load the raw dataset from a Parquet file.

    Args:
        file_path: Path to the input parquet file.

    Returns:
        pandas DataFrame containing the dataset.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw dataset file not found: {file_path}")

    try:
        df = pd.read_parquet(path)
        logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns.")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def load_cleaned_dataset(file_path: str) -> pd.DataFrame:
    """
    Load the cleaned dataset (post-fidelity loss filtering) from a Parquet file.

    Args:
        file_path: Path to the cleaned parquet file.

    Returns:
        pandas DataFrame.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Cleaned dataset file not found: {file_path}")

    try:
        df = pd.read_parquet(path)
        logger.info(f"Loaded cleaned dataset with {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to load cleaned dataset: {e}")
        raise

# --- Data Extraction ---

def extract_teacher_scores_matrix(df: pd.DataFrame) -> np.ndarray:
    """
    Extract the N x 4 matrix of teacher scores for the four rubric dimensions.

    Expected columns (or keys in 'teacher_scores' object column if structured):
    Alignment, Realism, Aesthetics, Plausibility

    Args:
        df: Input DataFrame.

    Returns:
        numpy array of shape (N, 4).
    """
    dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]

    # Check if teacher_scores is a nested object column or flat columns
    if "teacher_scores" in df.columns:
        # It's likely a dict-like object per row
        try:
            matrix = df["teacher_scores"].apply(
                lambda x: [float(x[d]) for d in dimensions]
            ).values
            matrix = np.vstack(matrix)
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Failed to extract teacher scores from nested column: {e}")
            raise
    else:
        # Assume flat columns: teacher_Alignment, etc. or just Alignment
        # Based on schema in T001d, it's likely nested, but we handle flat as fallback
        cols = [f"teacher_{d}" if f"teacher_{d}" in df.columns else d for d in dimensions]
        if not all(c in df.columns for c in cols):
            # Fallback: try just the dimension names directly
            cols = dimensions
            if not all(c in df.columns for c in cols):
                raise ValueError(
                    f"Could not find teacher score columns. Expected one of: "
                    f"{[f'teacher_{d}' for d in dimensions] + dimensions}"
                )

        matrix = df[cols].astype(float).values

    if matrix.shape[1] != 4:
        raise ValueError(f"Expected 4 dimensions, got {matrix.shape[1]}")

    return matrix

# --- Statistical Helpers ---

def calculate_variance_and_range(values: np.ndarray) -> Tuple[float, float]:
    """
    Calculate variance and range for a 1D array of values.

    Args:
        values: 1D numpy array.

    Returns:
        Tuple of (variance, range).
    """
    if len(values) == 0:
        return 0.0, 0.0
    var = np.var(values, ddof=0)  # Population variance for consistency
    range_val = float(np.max(values) - np.min(values))
    return float(var), range_val

def calculate_entropy(values: np.ndarray) -> float:
    """
    Calculate Shannon entropy for a 1D array of values.
    Treats the values as a distribution by binning if necessary,
    or calculates differential entropy if continuous.
    For this task, we assume the values represent a distribution of scores
    and calculate entropy based on normalized probabilities.

    To handle continuous scores, we discretize (bin) them.
    """
    if len(values) == 0:
        return 0.0

    # If variance is 0, entropy is 0
    if np.var(values) == 0:
        return 0.0

    # Discretize into bins to calculate probability distribution
    # Using a fixed number of bins or auto-bin
    try:
        counts, _ = np.histogram(values, bins="auto")
        # Normalize to probabilities
        probs = counts / counts.sum()
        # Filter out zeros to avoid log(0)
        probs = probs[probs > 0]
        entropy = -np.sum(probs * np.log2(probs))
        return float(entropy)
    except Exception:
        # Fallback for edge cases
        return 0.0

def calculate_skewness_and_kurtosis(values: np.ndarray) -> Tuple[float, float]:
    """
    Calculate skewness and kurtosis for a 1D array.

    Returns:
        Tuple of (skewness, kurtosis).
    """
    if len(values) < 3:
        return 0.0, 0.0

    try:
        skew = float(scipy.stats.skew(values))
        kurt = float(scipy.stats.kurtosis(values))
        return skew, kurt
    except Exception:
        return 0.0, 0.0

def calculate_global_covariance_and_eigenvalue(matrix: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Calculate the global covariance matrix and its dominant eigenvalue.

    Args:
        matrix: N x 4 numpy array of teacher scores.

    Returns:
        Tuple of (covariance_matrix, dominant_eigenvalue).
    """
    if matrix.shape[0] < 2:
        logger.warning("Insufficient samples for covariance calculation.")
        return np.zeros((4, 4)), 0.0

    # rowvar=False means columns are variables (dimensions), rows are observations
    cov_matrix = np.cov(matrix, rowvar=False)

    # Compute eigenvalues
    eigenvalues, _ = np.linalg.eig(cov_matrix)

    # Dominant eigenvalue is the largest (real part, assuming real matrix)
    dominant_eigenvalue = float(np.max(np.real(eigenvalues)))

    return cov_matrix, dominant_eigenvalue

def compute_per_sample_stats(matrix: np.ndarray) -> pd.DataFrame:
    """
    Compute per-sample statistical descriptors (Variance, Entropy, Skewness, Kurtosis)
    for the 4-dimensional teacher score vector of each sample.

    Args:
        matrix: N x 4 numpy array.

    Returns:
        DataFrame with columns: variance, entropy, skewness, kurtosis.
    """
    n_samples = matrix.shape[0]
    stats = {
        "variance": [],
        "entropy": [],
        "skewness": [],
        "kurtosis": []
    }

    for i in range(n_samples):
        vec = matrix[i, :]
        var_val, _ = calculate_variance_and_range(vec)
        ent_val = calculate_entropy(vec)
        skew_val, kurt_val = calculate_skewness_and_kurtosis(vec)

        stats["variance"].append(var_val)
        stats["entropy"].append(ent_val)
        stats["skewness"].append(skew_val)
        stats["kurtosis"].append(kurt_val)

    return pd.DataFrame(stats)

def integrate_features(df: pd.DataFrame, features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Integrate calculated features into the main dataframe.

    Args:
        df: Original DataFrame.
        features_df: DataFrame with per-sample stats.

    Returns:
        Combined DataFrame.
    """
    if len(df) != len(features_df):
        raise ValueError(
            f"Length mismatch: Original ({len(df)}) vs Features ({len(features_df)})"
        )
    return pd.concat([df.reset_index(drop=True), features_df.reset_index(drop=True)], axis=1)

def save_global_stats(cov_matrix: np.ndarray, dominant_eigenvalue: float, results_dir: Path):
    """
    Save global covariance matrix and dominant eigenvalue to JSON files.

    Args:
        cov_matrix: 4x4 numpy array.
        dominant_eigenvalue: float.
        results_dir: Path to results directory.
    """
    # Save Covariance Matrix
    cov_path = results_dir / "covariance_matrix.json"
    with open(cov_path, "w") as f:
        json.dump(cov_matrix.tolist(), f, indent=2)
    logger.info(f"Covariance matrix saved to {cov_path}")

    # Save Dominant Eigenvalue
    eig_path = results_dir / "dominant_eigenvalue.json"
    with open(eig_path, "w") as f:
        json.dump({"dominant_eigenvalue": dominant_eigenvalue}, f, indent=2)
    logger.info(f"Dominant eigenvalue saved to {eig_path}")

def save_features_to_csv(df: pd.DataFrame, output_path: str):
    """Save the feature-enriched dataframe to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Features saved to {output_path}")

# --- Argument Parsing ---

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute entanglement features and global covariance metrics."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input cleaned parquet file. If None, defaults to cleaned_data.parquet."
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default=None,
        help="Path to output CSV for features. If None, defaults to entanglement_scores.csv."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level."
    )
    return parser.parse_args()

# --- Main Execution ---

def main():
    args = parse_args()
    log_level = getattr(logging, args.log_level.upper())
    logger.setLevel(log_level)

    raw_dir, processed_dir, results_dir = setup_directories()

    # Determine input file
    input_file = args.input or str(processed_dir / "cleaned_data.parquet")
    output_csv = args.output_csv or str(processed_dir / "entanglement_scores.csv")

    logger.info(f"Processing input: {input_file}")

    try:
        # 1. Load Data
        df = load_cleaned_dataset(input_file)

        # 2. Extract Teacher Scores
        matrix = extract_teacher_scores_matrix(df)

        # 3. Compute Global Covariance (Required for Mahalanobis later, and global hypothesis)
        cov_matrix, dominant_eigenvalue = calculate_global_covariance_and_eigenvalue(matrix)
        save_global_stats(cov_matrix, dominant_eigenvalue, results_dir)

        # 4. Compute Per-Sample Stats
        # Note: T022a requires Variance, Entropy, Skewness, Kurtosis per sample.
        # T022c requires Mahalanobis Distance (computed in separate module or here).
        # This function focuses on the statistical descriptors as per T006 skeleton.
        features_df = compute_per_sample_stats(matrix)

        # 5. Integrate and Save
        final_df = integrate_features(df, features_df)
        save_features_to_csv(final_df, output_csv)

        logger.info("Feature engineering completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during feature engineering: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
