"""
Feature Engineering Module for llmXive Entanglement Analysis.

This module implements statistical descriptors for teacher distributions
and calculates global entanglement scores across the dataset.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_aligned_data(input_path: str) -> pd.DataFrame:
    """
    Load aligned data from the ingestion step.

    Args:
        input_path: Path to the JSON file containing aligned data.

    Returns:
        DataFrame with aligned data.
    """
    logger.info(f"Loading aligned data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r') as f:
        data = json.load(f)

    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame([data])

    logger.info(f"Loaded {len(df)} samples")
    return df


def calculate_variance_and_range(logits: List[float]) -> Dict[str, float]:
    """
    Calculate variance and range for a list of logits.

    Args:
        logits: List of teacher logits for 4 dimensions.

    Returns:
        Dictionary with 'variance' and 'range' keys.
    """
    if not logits or len(logits) != 4:
        raise ValueError("Logits must be a list of 4 floats")

    arr = np.array(logits, dtype=np.float64)

    # Handle zero-variance case
    if np.all(arr == arr[0]):
        variance = 0.0
        range_val = 0.0
    else:
        variance = float(np.var(arr))
        range_val = float(np.max(arr) - np.min(arr))

    return {
        'variance': variance,
        'range': range_val
    }


def calculate_entropy(logits: List[float]) -> float:
    """
    Calculate entropy for a list of logits.

    Args:
        logits: List of teacher logits for 4 dimensions.

    Returns:
        Entropy value (0 if zero-variance).
    """
    if not logits or len(logits) != 4:
        raise ValueError("Logits must be a list of 4 floats")

    arr = np.array(logits, dtype=np.float64)

    # Convert logits to probabilities via softmax
    # Handle numerical stability
    max_logit = np.max(arr)
    exp_arr = np.exp(arr - max_logit)
    probs = exp_arr / np.sum(exp_arr)

    # Handle zero-variance case (all logits equal -> uniform distribution)
    # If all logits are equal, entropy is log(4) for 4 dimensions
    if np.all(arr == arr[0]):
        # Uniform distribution over 4 categories
        return float(np.log(4.0))

    # Calculate entropy: -sum(p * log(p))
    # Filter out zero probabilities to avoid log(0)
    valid_probs = probs[probs > 0]
    entropy = -np.sum(valid_probs * np.log(valid_probs))

    return float(entropy)


def calculate_skewness_and_kurtosis(logits: List[float]) -> Dict[str, float]:
    """
    Calculate skewness and kurtosis for a list of logits.

    Args:
        logits: List of teacher logits for 4 dimensions.

    Returns:
        Dictionary with 'skewness' and 'kurtosis' keys.
    """
    if not logits or len(logits) != 4:
        raise ValueError("Logits must be a list of 4 floats")

    arr = np.array(logits, dtype=np.float64)

    # Handle zero-variance case
    if np.all(arr == arr[0]):
        return {
            'skewness': 0.0,
            'kurtosis': 0.0
        }

    # Calculate skewness and kurtosis
    skewness = float(scipy.stats.skew(arr))
    kurtosis = float(scipy.stats.kurtosis(arr))

    return {
        'skewness': skewness,
        'kurtosis': kurtosis
    }


def calculate_per_sample_stats(logits: List[float]) -> Dict[str, Any]:
    """
    Calculate all per-sample statistics for a single sample.

    Args:
        logits: List of teacher logits for 4 dimensions.

    Returns:
        Dictionary with variance, range, entropy, skewness, and kurtosis.
    """
    var_range = calculate_variance_and_range(logits)
    entropy = calculate_entropy(logits)
    skew_kurt = calculate_skewness_and_kurtosis(logits)

    return {
        'variance': var_range['variance'],
        'range': var_range['range'],
        'entropy': entropy,
        'skewness': skew_kurt['skewness'],
        'kurtosis': skew_kurt['kurtosis']
    }


def calculate_global_entanglement_score(df: pd.DataFrame) -> float:
    """
    Calculate the global dominant eigenvalue of the teacher's score distribution.

    This computes the covariance matrix of the teacher's 4-dimensional score
    vector across the entire dataset and extracts the dominant (largest) eigenvalue.

    Args:
        df: DataFrame containing teacher logits.

    Returns:
        Dominant eigenvalue (dataset-wide entanglement score).
    """
    if df.empty:
        raise ValueError("DataFrame is empty")

    # Extract teacher logits column
    if 'teacher_logits' not in df.columns:
        raise ValueError("DataFrame must contain 'teacher_logits' column")

    # Convert list of logits to 2D array
    logits_array = np.array(df['teacher_logits'].tolist(), dtype=np.float64)

    if logits_array.shape[1] != 4:
        raise ValueError("Teacher logits must have 4 dimensions")

    # Calculate covariance matrix (4x4)
    # Each row is a sample, each column is a dimension
    cov_matrix = np.cov(logits_array, rowvar=False)

    # Calculate eigenvalues
    eigenvalues = np.linalg.eigvals(cov_matrix)

    # Get dominant (largest) eigenvalue
    dominant_eigenvalue = float(np.max(np.real(eigenvalues)))

    # Validate output is finite and non-NaN
    if not np.isfinite(dominant_eigenvalue):
        raise ValueError(f"Dominant eigenvalue is not finite: {dominant_eigenvalue}")

    logger.info(f"Global covariance matrix shape: {cov_matrix.shape}")
    logger.info(f"Dominant eigenvalue (entanglement score): {dominant_eigenvalue:.6f}")

    return dominant_eigenvalue


def calculate_dimensional_fidelity_loss(
    df: pd.DataFrame,
    primary_dimension: str
) -> pd.DataFrame:
    """
    Calculate dimensional fidelity loss (MAE) between student scalar and human annotation.

    Args:
        df: DataFrame with student_scalar and human_annotations.
        primary_dimension: The dimension to use for fidelity calculation.

    Returns:
        DataFrame with added 'fidelity_loss' column.
    """
    if 'student_scalar' not in df.columns:
        raise ValueError("DataFrame must contain 'student_scalar' column")

    if 'human_annotations' not in df.columns:
        raise ValueError("DataFrame must contain 'human_annotations' column")

    def compute_fidelity_loss(row):
        student_score = row['student_scalar']
        annotations = row['human_annotations']

        if not isinstance(annotations, dict):
            return np.nan

        if primary_dimension not in annotations:
            return np.nan

        human_score = annotations[primary_dimension]

        if student_score is None or human_score is None:
            return np.nan

        return abs(student_score - human_score)

    df['fidelity_loss'] = df.apply(compute_fidelity_loss, axis=1)

    # Log missing values
    missing_count = df['fidelity_loss'].isna().sum()
    logger.info(f"Samples with missing fidelity loss: {missing_count}")

    return df


def compute_all_features(df: pd.DataFrame, primary_dimension: str) -> Tuple[pd.DataFrame, float]:
    """
    Compute all features for the dataset.

    Args:
        df: DataFrame with aligned data.
        primary_dimension: Primary quality dimension for fidelity loss.

    Returns:
        Tuple of (DataFrame with features, global entanglement score).
    """
    logger.info("Computing per-sample statistics...")

    # Calculate per-sample stats
    stats_list = []
    for idx, row in df.iterrows():
        if 'teacher_logits' not in row or not row['teacher_logits']:
            stats_list.append({
                'sample_id': row.get('sample_id', idx),
                'variance': np.nan,
                'range': np.nan,
                'entropy': np.nan,
                'skewness': np.nan,
                'kurtosis': np.nan
            })
        else:
            stats = calculate_per_sample_stats(row['teacher_logits'])
            stats['sample_id'] = row.get('sample_id', idx)
            stats_list.append(stats)

    stats_df = pd.DataFrame(stats_list)

    # Merge stats back to main dataframe
    df = df.merge(stats_df, on='sample_id', how='left')

    # Calculate global entanglement score
    logger.info("Computing global entanglement score...")
    global_entanglement = calculate_global_entanglement_score(df)

    # Calculate fidelity loss
    logger.info("Calculating dimensional fidelity loss...")
    df = calculate_dimensional_fidelity_loss(df, primary_dimension)

    # Add global entanglement to all rows
    df['dominant_eigenvalue'] = global_entanglement

    return df, global_entanglement


def save_features_to_json(df: pd.DataFrame, output_path: str) -> None:
    """
    Save features to JSON file.

    Args:
        df: DataFrame with computed features.
        output_path: Path to output JSON file.
    """
    logger.info(f"Saving features to {output_path}")

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Convert DataFrame to list of dicts
    features = df.to_dict(orient='records')

    with open(output_path, 'w') as f:
        json.dump(features, f, indent=2)

    logger.info(f"Saved {len(features)} feature records")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Compute entanglement features from aligned data'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/processed/aligned_data.json',
        help='Path to aligned data JSON file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/features.json',
        help='Path to output features JSON file'
    )
    parser.add_argument(
        '--primary-dimension',
        type=str,
        default='Alignment',
        help='Primary quality dimension for fidelity loss'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for feature engineering."""
    args = parse_args()

    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    logger.info("Starting feature engineering pipeline")

    try:
        # Load aligned data
        df = load_aligned_data(args.input)

        # Compute all features
        df_features, global_score = compute_all_features(df, args.primary_dimension)

        # Save features
        save_features_to_json(df_features, args.output)

        logger.info(f"Feature engineering completed. Global entanglement score: {global_score:.6f}")

    except Exception as e:
        logger.error(f"Feature engineering failed: {e}")
        raise


if __name__ == '__main__':
    main()