import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# Logging setup
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def calculate_entropy(probabilities):
    """
    Calculate Shannon entropy from a probability distribution.
    Handles zero probabilities to avoid log(0).
    
    Args:
        probabilities (np.ndarray): Array of probabilities (must sum to 1).
        
    Returns:
        float: Shannon entropy value.
    """
    # Filter out zeros to avoid log(0)
    non_zero_probs = probabilities[probabilities > 0]
    if len(non_zero_probs) == 0:
        return 0.0
    return -np.sum(non_zero_probs * np.log(non_zero_probs))

def compute_per_sample_stats(df):
    """
    Compute per-sample entanglement scores (Variance, Entropy, Skewness, Kurtosis)
    for the 4-dimensional teacher score vector.
    
    Args:
        df (pd.DataFrame): DataFrame containing teacher scores columns.
        
    Returns:
        pd.DataFrame: DataFrame with new columns:
            - variance: Variance of the 4 scores
            - entropy: Normalized Shannon entropy
            - skewness: Skewness of the distribution
            - kurtosis: Kurtosis of the distribution
    """
    # Expected columns for teacher scores
    score_columns = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
    
    # Ensure columns exist
    missing_cols = [col for col in score_columns if col not in df.columns]
    if missing_cols:
        raise RuntimeError(f"Missing required teacher score columns: {missing_cols}")
    
    # Extract the matrix of scores (N samples x 4 dimensions)
    scores_matrix = df[score_columns].values.astype(float)
    
    # Handle NaNs: if any row has NaN, we will set stats to 0 or NaN depending on policy
    # For this implementation, if a row has any NaN, we set variance=0, entropy=0, skew=NaN, kurt=NaN
    # and log a warning.
    nan_mask = np.isnan(scores_matrix).any(axis=1)
    
    # Initialize result arrays
    variances = np.zeros(len(df))
    entropies = np.zeros(len(df))
    skewnesses = np.full(len(df), np.nan)
    kurtoses = np.full(len(df), np.nan)
    
    # Process rows without NaNs
    valid_indices = ~nan_mask
    if np.any(valid_indices):
        valid_scores = scores_matrix[valid_indices]
        
        # Variance (axis=1)
        variances[valid_indices] = np.var(valid_scores, axis=1, ddof=0)
        
        # Skewness and Kurtosis
        # scipy.stats.skew and kurtosis default to ddof=0 for population
        skewnesses[valid_indices] = stats.skew(valid_scores, axis=1, bias=False)
        kurtoses[valid_indices] = stats.kurtosis(valid_scores, axis=1, fisher=False, bias=False)
        
        # Entropy calculation
        # Normalize each row to sum to 1 to treat as a probability distribution
        row_sums = valid_scores.sum(axis=1, keepdims=True)
        # Avoid division by zero
        safe_sums = np.where(row_sums == 0, 1, row_sums)
        prob_distributions = valid_scores / safe_sums
        
        # Calculate entropy for each row
        entropies[valid_indices] = np.apply_along_axis(calculate_entropy, 1, prob_distributions)
    
    # Log warning for NaN rows
    if np.any(nan_mask):
        logger.warning(f"Found {np.sum(nan_mask)} rows with NaN in teacher scores. "
                       "Set variance=0, entropy=0, skewness/kurtosis=NaN for these rows.")
    
    # Create new DataFrame or add columns
    df_out = df.copy()
    df_out['variance'] = variances
    df_out['entropy'] = entropies
    df_out['skewness'] = skewnesses
    df_out['kurtosis'] = kurtoses
    
    return df_out

def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute per-sample entanglement scores from teacher distributions."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input parquet file (output of T012: data/processed/raw_data.parquet)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output CSV file (data/processed/entanglement_scores.csv)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        raise

    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")

    logger.info("Computing per-sample entanglement scores...")
    df_result = compute_per_sample_stats(df)

    logger.info(f"Writing results to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_result.to_csv(output_path, index=False)

    logger.info("Done.")

if __name__ == "__main__":
    main()
