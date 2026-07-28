import argparse
import json
import logging
import math
import os
import sys
import numpy as np
import pandas as pd

def setup_logging():
    """Configure logging for the features module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def calculate_variance_and_range(values):
    """Calculate variance and range for a list of values."""
    if not values or len(values) < 2:
        return 0.0, 0.0
    arr = np.array(values, dtype=float)
    var = np.var(arr)
    range_val = np.max(arr) - np.min(arr)
    return var, range_val

def calculate_entropy(values):
    """Calculate Shannon entropy for a list of values (normalized to sum=1)."""
    if not values:
        return 0.0
    arr = np.array(values, dtype=float)
    if np.all(arr == 0):
        return 0.0
    p = arr / np.sum(arr)
    # Filter out zeros to avoid log(0)
    p = p[p > 0]
    if len(p) == 0:
        return 0.0
    entropy = -np.sum(p * np.log(p))
    return entropy

def calculate_skewness_and_kurtosis(values):
    """Calculate skewness and kurtosis for a list of values."""
    if not values or len(values) < 4:
        return 0.0, 0.0
    arr = np.array(values, dtype=float)
    if np.std(arr) == 0:
        return 0.0, 0.0
    skew = scipy.stats.skew(arr)
    kurt = scipy.stats.kurtosis(arr)
    return skew, kurt

def calculate_per_sample_stats(row, score_columns):
    """Calculate per-sample statistics (variance, entropy, skewness, kurtosis)."""
    scores = [row.get(col, 0.0) for col in score_columns]
    # Handle NaNs
    scores = [0.0 if math.isnan(s) else s for s in scores]
    
    variance, _ = calculate_variance_and_range(scores)
    entropy = calculate_entropy(scores)
    skewness, kurtosis = calculate_skewness_and_kurtosis(scores)
    
    return {
        'variance': variance,
        'entropy': entropy,
        'skewness': skewness,
        'kurtosis': kurtosis
    }

def calculate_global_covariance_and_eigenvalue(df, score_columns):
    """
    Calculate the global covariance matrix of teacher scores across the entire dataset
    and return the dominant eigenvalue (largest eigenvalue).
    
    Args:
        df: DataFrame containing the data
        score_columns: List of column names corresponding to teacher score dimensions
    
    Returns:
        float: The dominant eigenvalue
    """
    # Extract the relevant columns, handling potential NaNs
    data_matrix = df[score_columns].dropna()
    
    if data_matrix.empty:
        logging.warning("No valid data for covariance calculation. Returning 0.0.")
        return 0.0
    
    # Calculate covariance matrix
    cov_matrix = np.cov(data_matrix.values.T)
    
    # Calculate eigenvalues
    eigenvalues = np.linalg.eigvals(cov_matrix)
    
    # Get the dominant (largest) eigenvalue
    dominant_eigenvalue = np.max(np.real(eigenvalues))
    
    return float(dominant_eigenvalue)

def calculate_dominant_eigenvalue(df, score_columns):
    """
    Wrapper to calculate and return the dominant eigenvalue for the global covariance.
    
    Args:
        df (pd.DataFrame): The dataset
        score_columns (list): List of column names for teacher scores
    
    Returns:
        float: The dominant eigenvalue
    """
    return calculate_global_covariance_and_eigenvalue(df, score_columns)

def calculate_frobenius_norm_outer_product(matrix):
    """Calculate the Frobenius norm of an outer product matrix."""
    if matrix is None or len(matrix) == 0:
        return 0.0
    arr = np.array(matrix)
    if arr.ndim == 1:
        # Outer product of vector with itself
        outer = np.outer(arr, arr)
    else:
        outer = arr
    return np.linalg.norm(outer, 'fro')

def calculate_fidelity_loss(student_scalar, human_annotation, primary_dimension):
    """Calculate fidelity loss (MAE) between student and human for the primary dimension."""
    if primary_dimension not in human_annotation:
        return None
    human_score = human_annotation[primary_dimension]
    if math.isnan(human_score) or math.isnan(student_scalar):
        return None
    return abs(student_scalar - human_score)

def load_features_from_json(filepath):
    """Load features from a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def save_features_to_json(features, filepath):
    """Save features to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(features, f, indent=2)

def compute_global_stats(df, score_columns):
    """Compute global statistics (mean, std) for each score dimension."""
    stats = {}
    for col in score_columns:
        data = df[col].dropna()
        stats[col] = {
            'mean': float(np.mean(data)) if not data.empty else 0.0,
            'std': float(np.std(data)) if not data.empty else 0.0
        }
    return stats

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Feature Engineering for Entanglement Analysis')
    parser.add_argument('--input', type=str, required=True, help='Input data file (parquet)')
    parser.add_argument('--output', type=str, required=True, help='Output features file (json)')
    parser.add_argument('--score-columns', type=str, nargs='+', 
                        default=['Alignment', 'Realism', 'Aesthetics', 'Plausibility'],
                        help='Columns representing teacher score dimensions')
    return parser.parse_args()

def main():
    """Main entry point for feature engineering."""
    logger = setup_logging()
    args = parse_args()
    
    logger.info(f"Loading data from {args.input}")
    try:
        df = pd.read_parquet(args.input)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    logger.info(f"Calculating per-sample stats for columns: {args.score_columns}")
    
    # Calculate per-sample stats
    per_sample_stats = df.apply(
        lambda row: calculate_per_sample_stats(row, args.score_columns), 
        axis=1
    )
    
    # Calculate global dominant eigenvalue
    logger.info("Calculating global dominant eigenvalue...")
    dominant_eigenvalue = calculate_dominant_eigenvalue(df, args.score_columns)
    logger.info(f"Dominant Eigenvalue: {dominant_eigenvalue}")
    
    # Merge stats into dataframe
    for stat in ['variance', 'entropy', 'skewness', 'kurtosis']:
        df[stat] = per_sample_stats.apply(lambda x: x[stat])
    
    # Broadcast dominant eigenvalue to all rows
    df['dominant_eigenvalue'] = dominant_eigenvalue
    
    # Save results
    logger.info(f"Saving features to {args.output}")
    df.to_parquet(args.output, index=False)
    
    logger.info("Feature engineering complete.")

if __name__ == '__main__':
    main()
