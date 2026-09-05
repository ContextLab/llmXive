"""
Feature Engineering Module for llmXive Follow-up Project.

This module provides statistical helper functions for calculating
entanglement features (variance, entropy, skewness, kurtosis)
and global covariance metrics from teacher score distributions.
"""

import argparse
import json
import logging
import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = PROJECT_ROOT / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala"

# Constants
TEACHER_SCORE_COLS = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
DEFAULT_INPUT_PATH = PROJECT_DIR / "data" / "raw" / "z_reward.parquet"
DEFAULT_OUTPUT_PATH = PROJECT_DIR / "data" / "processed" / "features.json"
DEFAULT_GLOBAL_STATS_PATH = PROJECT_DIR / "results" / "covariance_matrix.json"


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure and return the project logger."""
    logger = logging.getLogger("llmxive_features")
    logger.setLevel(log_level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def setup_directories() -> None:
    """Ensure all necessary output directories exist."""
    dirs = [
        PROJECT_DIR / "data" / "raw",
        PROJECT_DIR / "data" / "processed",
        PROJECT_DIR / "results",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def load_raw_dataset(
    path: Optional[Path] = None, logger: Optional[logging.Logger] = None
) -> pd.DataFrame:
    """
    Load the raw dataset from a Parquet file.

    Args:
        path: Path to the parquet file. Defaults to DEFAULT_INPUT_PATH.
        logger: Optional logger instance.

    Returns:
        Loaded pandas DataFrame.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if logger is None:
        logger = setup_logging()

    if path is None:
        path = DEFAULT_INPUT_PATH

    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    logger.info(f"Loading dataset from {path}")
    df = pd.read_parquet(path)

    # Validate presence of teacher score columns
    missing_cols = [c for c in TEACHER_SCORE_COLS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required teacher score columns: {missing_cols}. "
            f"Found columns: {list(df.columns)}"
        )

    logger.info(f"Loaded {len(df)} samples with columns: {list(df.columns)}")
    return df


def extract_teacher_scores_matrix(
    df: pd.DataFrame,
    logger: Optional[logging.Logger] = None,
) -> np.ndarray:
    """
    Extract the N x 4 matrix of teacher scores.

    Args:
        df: Input DataFrame.
        logger: Optional logger instance.

    Returns:
        Numpy array of shape (N, 4).
    """
    if logger is None:
        logger = setup_logging()

    matrix = df[TEACHER_SCORE_COLS].to_numpy(dtype=float)
    logger.debug(f"Extracted teacher scores matrix shape: {matrix.shape}")
    return matrix


def calculate_variance_and_range(
    scores: np.ndarray,
) -> Tuple[float, float]:
    """
    Calculate variance and range for a 1D array of scores.

    Args:
        scores: 1D numpy array of scores.

    Returns:
        Tuple of (variance, range).
    """
    if len(scores) == 0:
        return 0.0, 0.0

    variance = float(np.var(scores, ddof=0))
    range_val = float(np.max(scores) - np.min(scores))
    return variance, range_val


def calculate_entropy(
    scores: np.ndarray,
    epsilon: float = 1e-10,
) -> float:
    """
    Calculate Shannon entropy for a 1D array of scores.

    Normalizes scores to a probability distribution before calculating entropy.
    Handles zero-variance cases by returning 0.

    Args:
        scores: 1D numpy array of scores.
        epsilon: Small constant to avoid log(0).

    Returns:
        Entropy value.
    """
    if len(scores) == 0:
        return 0.0

    # Normalize to probability distribution
    min_val = np.min(scores)
    max_val = np.max(scores)
    range_val = max_val - min_val

    if range_val < epsilon:
        # Zero variance case
        return 0.0

    # Shift and scale to [0, 1] then normalize to sum to 1
    # We treat the values themselves as a distribution proxy
    # A common approach for continuous values is to bin or use the values directly
    # Here we normalize the vector to sum to 1 to treat as probabilities
    normalized = scores - min_val
    total = np.sum(normalized)

    if total < epsilon:
        return 0.0

    probs = normalized / total
    probs = np.clip(probs, epsilon, 1.0)
    entropy = -np.sum(probs * np.log(probs))
    return float(entropy)


def calculate_skewness_and_kurtosis(
    scores: np.ndarray,
) -> Tuple[float, float]:
    """
    Calculate skewness and kurtosis for a 1D array of scores.

    Args:
        scores: 1D numpy array of scores.

    Returns:
        Tuple of (skewness, kurtosis).
    """
    if len(scores) < 3:
        return 0.0, 0.0

    skew = float(stats.skew(scores, bias=False))
    kurt = float(stats.kurtosis(scores, bias=False))
    return skew, kurt


def compute_per_sample_stats(
    df: pd.DataFrame,
    logger: Optional[logging.Logger] = None,
) -> pd.DataFrame:
    """
    Compute per-sample statistical descriptors (variance, entropy, skewness, kurtosis).

    Args:
        df: Input DataFrame.
        logger: Optional logger instance.

    Returns:
        DataFrame with added statistical columns.
    """
    if logger is None:
        logger = setup_logging()

    logger.info("Computing per-sample statistics...")
    df = df.copy()

    # Initialize columns
    df["variance"] = 0.0
    df["entropy"] = 0.0
    df["skewness"] = 0.0
    df["kurtosis"] = 0.0

    for idx, row in df.iterrows():
        scores = row[TEACHER_SCORE_COLS].values.astype(float)
        var, rng = calculate_variance_and_range(scores)
        ent = calculate_entropy(scores)
        skew, kurt = calculate_skewness_and_kurtosis(scores)

        df.at[idx, "variance"] = var
        df.at[idx, "entropy"] = ent
        df.at[idx, "skewness"] = skew
        df.at[idx, "kurtosis"] = kurt

    logger.info(f"Computed stats for {len(df)} samples.")
    return df


def calculate_global_covariance_and_eigenvalue(
    matrix: np.ndarray,
    logger: Optional[logging.Logger] = None,
) -> Tuple[np.ndarray, float]:
    """
    Calculate the global covariance matrix and dominant eigenvalue.

    Args:
        matrix: N x 4 matrix of teacher scores.
        logger: Optional logger instance.

    Returns:
        Tuple of (covariance_matrix, dominant_eigenvalue).
    """
    if logger is None:
        logger = setup_logging()

    logger.info("Calculating global covariance matrix...")
    # Compute covariance matrix (rowvar=False implies columns are variables)
    cov_matrix = np.cov(matrix, rowvar=False)

    # Compute eigenvalues
    eigenvalues, _ = np.linalg.eigh(cov_matrix)
    dominant_eigenvalue = float(np.max(eigenvalues))

    logger.info(f"Dominant eigenvalue: {dominant_eigenvalue}")
    return cov_matrix, dominant_eigenvalue


def save_global_stats(
    cov_matrix: np.ndarray,
    dominant_eigenvalue: float,
    output_path: Optional[Path] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Save global covariance matrix and eigenvalue to JSON.

    Args:
        cov_matrix: Covariance matrix.
        dominant_eigenvalue: Dominant eigenvalue.
        output_path: Output path. Defaults to DEFAULT_GLOBAL_STATS_PATH.
        logger: Optional logger instance.
    """
    if logger is None:
        logger = setup_logging()

    if output_path is None:
        output_path = PROJECT_DIR / "results" / "covariance_matrix.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "covariance_matrix": cov_matrix.tolist(),
        "dominant_eigenvalue": dominant_eigenvalue,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved global stats to {output_path}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Compute feature engineering statistics for llmXive."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_INPUT_PATH),
        help="Path to input parquet file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to output features JSON.",
    )
    parser.add_argument(
        "--global-stats-output",
        type=str,
        default=str(PROJECT_DIR / "results" / "covariance_matrix.json"),
        help="Path to output global stats JSON.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for feature engineering."""
    args = parse_args()
    logger = setup_logging(getattr(logging, args.log_level))

    try:
        setup_directories()

        # Load data
        df = load_raw_dataset(Path(args.input), logger)

        # Compute per-sample stats
        df_features = compute_per_sample_stats(df, logger)

        # Extract matrix for global stats
        matrix = extract_teacher_scores_matrix(df, logger)
        cov_matrix, dominant_eigenvalue = calculate_global_covariance_and_eigenvalue(
            matrix, logger
        )

        # Save global stats
        save_global_stats(
            cov_matrix,
            dominant_eigenvalue,
            Path(args.global_stats_output),
            logger,
        )

        # Prepare output features (convert to serializable format)
        features_list = df_features[
            ["variance", "entropy", "skewness", "kurtosis"]
        ].to_dict(orient="records")

        output_data = {
            "sample_count": len(features_list),
            "features": features_list,
        }

        # Save features
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Successfully wrote features to {args.output}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()