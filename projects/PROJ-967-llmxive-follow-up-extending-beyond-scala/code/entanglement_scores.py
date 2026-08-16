import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

def setup_logging(log_level=logging.INFO):
    """Configure logging for the entanglement scores module."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)

def calculate_entropy(probs):
    """
    Calculate Shannon entropy for a probability distribution.
    Handles zero probabilities by ignoring them (0 * log(0) = 0).

    Args:
        probs: 1D array of probabilities (must sum to 1).

    Returns:
        float: Shannon entropy.
    """
    # Filter out zeros to avoid log(0)
    non_zero_probs = probs[probs > 0]
    if len(non_zero_probs) == 0:
        return 0.0
    return -np.sum(non_zero_probs * np.log2(non_zero_probs))

def compute_per_sample_stats(teacher_scores):
    """
    Compute per-sample entanglement statistics: Variance, Entropy, Skewness, Kurtosis.

    Args:
        teacher_scores: 1D numpy array of 4 teacher scores (Alignment, Realism, Aesthetics, Plausibility).

    Returns:
        dict: Dictionary containing variance, entropy, skewness, kurtosis.
    """
    if teacher_scores.size == 0:
        return {"variance": 0.0, "entropy": 0.0, "skewness": 0.0, "kurtosis": 0.0}

    # Variance
    variance = np.var(teacher_scores)

    # Entropy: Normalize scores to probabilities
    # Handle negative scores or zeros by shifting or adding small epsilon if needed.
    # However, scores are usually positive in this context. If not, use softmax or absolute.
    # Given the context of "scores", we assume they are positive or can be normalized.
    # If they are raw logits, softmax is appropriate. If they are already scores (e.g., 1-10),
    # we normalize by sum.
    scores = teacher_scores
    score_sum = np.sum(scores)
    if score_sum == 0:
        # If sum is zero, probabilities are undefined. Set entropy to 0.
        entropy = 0.0
    else:
        probs = scores / score_sum
        entropy = calculate_entropy(probs)

    # Skewness and Kurtosis
    # Use scipy.stats for robust calculation, but fallback to numpy if not available
    try:
        from scipy.stats import skew, kurtosis
        skewness = skew(teacher_scores)
        kurtosis_val = kurtosis(teacher_scores)
    except ImportError:
        # Fallback manual calculation
        n = len(teacher_scores)
        mean = np.mean(teacher_scores)
        std = np.std(teacher_scores)
        if std == 0:
            skewness = 0.0
            kurtosis_val = 0.0
        else:
            skewness = np.mean(((teacher_scores - mean) / std) ** 3)
            kurtosis_val = np.mean(((teacher_scores - mean) / std) ** 4) - 3

    return {
        "variance": float(variance),
        "entropy": float(entropy),
        "skewness": float(skewness),
        "kurtosis": float(kurtosis_val),
    }

def load_cleaned_data(input_path):
    """
    Load the cleaned dataset from parquet.

    Args:
        input_path: Path to the cleaned data parquet file.

    Returns:
        pd.DataFrame: Loaded dataframe.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Cleaned data file not found: {input_path}")
    return pd.read_parquet(input_path)

def extract_teacher_scores_matrix(df, dimensions=["Alignment", "Realism", "Aesthetics", "Plausibility"]):
    """
    Extract the 4-dimensional teacher score vector for each sample.

    Args:
        df: DataFrame containing the data.
        dimensions: List of column names for teacher scores.

    Returns:
        np.ndarray: N x 4 matrix of teacher scores.
    """
    # Ensure columns exist
    missing_cols = [col for col in dimensions if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing teacher score columns: {missing_cols}")

    return df[dimensions].values.astype(float)

def integrate_features(df, stats_list, output_path):
    """
    Append calculated stats to the dataframe and write to CSV.

    Args:
        df: Original dataframe.
        stats_list: List of dictionaries containing per-sample stats.
        output_path: Path to write the output CSV.
    """
    # Create a DataFrame from stats
    stats_df = pd.DataFrame(stats_list)

    # Ensure index alignment if stats_df has same length as df
    if len(stats_df) != len(df):
        logging.warning(f"Stats length ({len(stats_df)}) does not match dataframe length ({len(df)}). Resetting index.")
        stats_df = stats_df.reset_index(drop=True)
        df = df.reset_index(drop=True)

    # Concatenate
    result_df = pd.concat([df, stats_df], axis=1)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write to CSV
    result_df.to_csv(output_path, index=False)
    logging.info(f"Entanglement scores written to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Compute per-sample entanglement scores.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/cleaned_data.parquet",
        help="Path to the cleaned data parquet file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/entanglement_scores.csv",
        help="Path to write the output CSV.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging(getattr(logging, args.log_level))

    logger.info(f"Loading cleaned data from {args.input}")
    df = load_cleaned_data(args.input)

    logger.info("Extracting teacher scores matrix")
    try:
        teacher_matrix = extract_teacher_scores_matrix(df)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info("Computing per-sample statistics")
    stats_list = []
    for i, row_scores in enumerate(teacher_matrix):
        stats = compute_per_sample_stats(row_scores)
        stats_list.append(stats)
        if i % 1000 == 0:
            logger.debug(f"Processed {i} samples")

    logger.info(f"Integrating features and writing to {args.output}")
    integrate_features(df, stats_list, args.output)

    logger.info("Done.")

if __name__ == "__main__":
    main()