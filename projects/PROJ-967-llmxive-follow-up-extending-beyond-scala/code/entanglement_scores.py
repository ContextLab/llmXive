"""
Entanglement Score Calculation Module (Task T022a)

Implements per-sample entanglement scores (variance, entropy, skewness, kurtosis)
and Mahalanobis distance using the global covariance matrix from T022b-filtered.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# Import shared utilities from existing API surface
from global_covariance import load_cleaned_data, extract_teacher_scores_matrix
from features import calculate_entropy

# Project root relative to code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
RESULTS = PROJECT_ROOT / "results"


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)


def load_dominant_eigenvalue(logger):
    """Load the global dominant eigenvalue from T022b-filtered."""
    eigenvalue_path = RESULTS / "dominant_eigenvalue.json"
    if not eigenvalue_path.exists():
        logger.error(f"Missing dominant eigenvalue file: {eigenvalue_path}. Run T022b-filtered first.")
        raise FileNotFoundError(f"Missing dominant eigenvalue file: {eigenvalue_path}")
    
    with open(eigenvalue_path, "r") as f:
        data = json.load(f)
    
    if "dominant_eigenvalue" not in data:
        logger.error("dominant_eigenvalue.json missing 'dominant_eigenvalue' key.")
        raise KeyError("dominant_eigenvalue.json missing 'dominant_eigenvalue' key.")
    
    return data["dominant_eigenvalue"]


def load_covariance_matrix(logger):
    """Load the global covariance matrix from T022b-filtered for Mahalanobis distance."""
    cov_path = RESULTS / "covariance_matrix.json"
    if not cov_path.exists():
        logger.error(f"Missing covariance matrix file: {cov_path}. Run T022b-filtered first.")
        raise FileNotFoundError(f"Missing covariance matrix file: {cov_path}")
    
    with open(cov_path, "r") as f:
        data = json.load(f)
    
    if "covariance_matrix" not in data:
        logger.error("covariance_matrix.json missing 'covariance_matrix' key.")
        raise KeyError("covariance_matrix.json missing 'covariance_matrix' key.")
    
    return np.array(data["covariance_matrix"])


def compute_per_sample_stats(df, teacher_matrix, logger):
    """
    Compute per-sample variance, entropy, skewness, and kurtosis.
    
    Args:
        df: DataFrame with teacher scores columns.
        teacher_matrix: N x 4 numpy array of teacher scores.
        logger: Logger instance.
        
    Returns:
        Dictionary of per-sample stats arrays.
    """
    n_samples = teacher_matrix.shape[0]
    n_dims = teacher_matrix.shape[1]
    
    logger.info(f"Computing per-sample stats for {n_samples} samples, {n_dims} dimensions.")
    
    # Variance (along dimensions for each sample)
    # teacher_matrix shape: (n_samples, n_dims) -> axis=1
    variance = np.var(teacher_matrix, axis=1, ddof=0)
    
    # Entropy (using scipy.stats.entropy, normalizing to probability distribution)
    # We treat the 4 teacher scores as a distribution. To handle negative scores or zeros,
    # we shift them to be positive or use a softmin/softmax if necessary.
    # However, typically entropy on raw scores isn't standard. 
    # Given the task description "Entropy... for teacher distributions", 
    # we assume the scores represent a distribution or we normalize them.
    # Strategy: Shift to positive, normalize to sum=1, then compute entropy.
    # If scores are negative, adding a constant to make them positive.
    min_vals = np.min(teacher_matrix, axis=1, keepdims=True)
    shifted_matrix = teacher_matrix - min_vals + 1e-9  # Ensure positive
    normalized_matrix = shifted_matrix / np.sum(shifted_matrix, axis=1, keepdims=True)
    
    # Avoid log(0)
    normalized_matrix = np.clip(normalized_matrix, 1e-10, 1.0)
    entropy = stats.entropy(normalized_matrix, axis=1)
    
    # Skewness (Fisher's definition, axis=1)
    skewness = stats.skew(teacher_matrix, axis=1, nan_policy='omit')
    
    # Kurtosis (Fisher's definition, axis=1)
    kurtosis = stats.kurtosis(teacher_matrix, axis=1, nan_policy='omit')
    
    return {
        "variance": variance,
        "entropy": entropy,
        "skewness": skewness,
        "kurtosis": kurtosis
    }


def compute_mahalanobis_distance(teacher_matrix, cov_matrix, logger):
    """
    Compute Mahalanobis distance for each sample using the global covariance matrix.
    
    D_M(x) = sqrt((x - mu)^T * Sigma^-1 * (x - mu))
    """
    n_samples = teacher_matrix.shape[0]
    
    # Compute global mean
    mu = np.mean(teacher_matrix, axis=0)
    
    # Use pseudo-inverse for singular matrices
    try:
        cov_inv = np.linalg.pinv(cov_matrix, rcond=1e-15)
    except np.linalg.LinAlgError as e:
        logger.warning(f"Could not invert covariance matrix, using pseudo-inverse: {e}")
        cov_inv = np.linalg.pinv(cov_matrix, rcond=1e-15)
    
    diff = teacher_matrix - mu
    
    # (x - mu)^T * Sigma^-1 * (x - mu)
    # diff shape: (n_samples, 4)
    # cov_inv shape: (4, 4)
    # result shape: (n_samples,)
    mahal_sq = np.einsum('ij,jk,ik->i', diff, cov_inv, diff)
    
    # Ensure non-negative due to numerical errors
    mahal_sq = np.maximum(mahal_sq, 0.0)
    mahalanobis = np.sqrt(mahal_sq)
    
    return mahalanobis


def integrate_features(df, stats_dict, mahalanobis, logger):
    """
    Integrate computed features into the DataFrame.
    """
    df["variance"] = stats_dict["variance"]
    df["entropy"] = stats_dict["entropy"]
    df["skewness"] = stats_dict["skewness"]
    df["kurtosis"] = stats_dict["kurtosis"]
    df["mahalanobis_distance"] = mahalanobis
    
    logger.info("Features integrated into DataFrame.")
    return df


def save_features(df, output_path, logger):
    """Save features to JSON."""
    # Select relevant columns
    features_df = df[["variance", "entropy", "skewness", "kurtosis", "mahalanobis_distance"]]
    
    # Convert to list of dicts
    records = features_df.to_dict(orient="records")
    
    with open(output_path, "w") as f:
        json.dump(records, f, indent=2)
    
    logger.info(f"Saved features to {output_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Compute per-sample entanglement scores.")
    parser.add_argument(
        "--input", 
        type=str, 
        default=str(DATA_PROCESSED / "cleaned_data.parquet"),
        help="Path to cleaned_data.parquet"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=str(DATA_PROCESSED / "features.json"),
        help="Path to output features.json"
    )
    return parser.parse_args()


def main():
    logger = setup_logging()
    args = parse_args()
    
    logger.info("Starting T022a: Per-Sample Entanglement Score Calculation")
    
    # 1. Load cleaned data
    logger.info(f"Loading cleaned data from {args.input}")
    df = load_cleaned_data(args.input, logger)
    
    if df is None or df.empty:
        logger.error("Cleaned data is empty or None. Cannot compute features.")
        sys.exit(1)
    
    # 2. Extract teacher scores matrix
    logger.info("Extracting teacher scores matrix.")
    teacher_matrix = extract_teacher_scores_matrix(df, logger)
    
    if teacher_matrix is None:
        logger.error("Failed to extract teacher scores matrix.")
        sys.exit(1)
    
    # 3. Load global covariance matrix and eigenvalue
    logger.info("Loading global covariance matrix and eigenvalue.")
    cov_matrix = load_covariance_matrix(logger)
    dominant_eigenvalue = load_dominant_eigenvalue(logger)
    logger.info(f"Global Dominant Eigenvalue: {dominant_eigenvalue}")
    
    # 4. Compute per-sample stats
    logger.info("Computing per-sample statistics.")
    stats_dict = compute_per_sample_stats(df, teacher_matrix, logger)
    
    # 5. Compute Mahalanobis distance
    logger.info("Computing Mahalanobis distance.")
    mahalanobis = compute_mahalanobis_distance(teacher_matrix, cov_matrix, logger)
    
    # 6. Integrate features
    df_features = integrate_features(df, stats_dict, mahalanobis, logger)
    
    # 7. Save features
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_features(df_features, output_path, logger)
    
    logger.info("T022a completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
