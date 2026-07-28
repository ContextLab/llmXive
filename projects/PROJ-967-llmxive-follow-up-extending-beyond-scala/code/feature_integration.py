import argparse
import json
import logging
import os
import sys
import numpy as np
import pandas as pd
from features import (
    calculate_per_sample_stats, 
    calculate_dominant_eigenvalue, 
    calculate_fidelity_loss
)

def setup_logging():
    """Configure logging for the integration module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def setup_directories(output_path):
    """Ensure the output directory exists."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.info(f"Created directory: {output_dir}")

def compute_global_eigenvalue(df, score_columns):
    """
    Compute the dominant eigenvalue of the global covariance matrix of teacher scores.
    
    This is a single scalar value for the entire dataset, representing the 
    "structural entanglement" of the teacher model.
    
    Args:
        df (pd.DataFrame): The dataset
        score_columns (list): List of column names for teacher scores
    
    Returns:
        float: The dominant eigenvalue
    """
    # Extract relevant columns, dropping rows with NaNs in any score dimension
    valid_data = df[score_columns].dropna()
    
    if valid_data.empty:
        logging.warning("No valid data for eigenvalue calculation. Returning 0.0.")
        return 0.0
    
    # Compute covariance matrix
    cov_matrix = np.cov(valid_data.values.T)
    
    # Compute eigenvalues
    eigenvalues = np.linalg.eigvals(cov_matrix)
    
    # Dominant eigenvalue is the largest real part
    dominant_eigenvalue = float(np.max(np.real(eigenvalues)))
    
    return dominant_eigenvalue

def compute_per_sample_frobenius_norm(row, score_columns):
    """Compute the Frobenius norm (L2 norm) of the score vector for a sample."""
    scores = [row.get(col, 0.0) for col in score_columns]
    # Handle NaNs
    scores = [0.0 if np.isnan(s) else s for s in scores]
    return float(np.linalg.norm(scores))

def integrate_features(input_path, output_path, score_columns):
    """
    Integrate all features into the dataframe:
    1. Per-sample stats (variance, entropy, skewness, kurtosis)
    2. Per-sample score magnitude (Frobenius norm)
    3. Global dominant eigenvalue (broadcast to all rows)
    
    Args:
        input_path (str): Path to input parquet file
        output_path (str): Path to output parquet file
        score_columns (list): List of column names for teacher scores
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Loading data from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows")
    
    # 1. Calculate per-sample stats
    logger.info("Calculating per-sample statistics...")
    per_sample_stats = df.apply(
        lambda row: calculate_per_sample_stats(row, score_columns), 
        axis=1
    )
    
    for stat in ['variance', 'entropy', 'skewness', 'kurtosis']:
        df[stat] = per_sample_stats.apply(lambda x: x[stat])
    
    # 2. Calculate per-sample score magnitude (Frobenius norm)
    logger.info("Calculating score magnitude (Frobenius norm)...")
    df['score_magnitude'] = df.apply(
        lambda row: compute_per_sample_frobenius_norm(row, score_columns), 
        axis=1
    )
    
    # 3. Calculate and broadcast global dominant eigenvalue
    logger.info("Calculating global dominant eigenvalue...")
    dominant_eigenvalue = compute_global_eigenvalue(df, score_columns)
    logger.info(f"Dominant Eigenvalue: {dominant_eigenvalue}")
    df['dominant_eigenvalue'] = dominant_eigenvalue
    
    # Save results
    setup_directories(output_path)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved integrated features to {output_path}")
    
    return df

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Integrate Entanglement Features')
    parser.add_argument('--input', type=str, required=True, help='Input parquet file')
    parser.add_argument('--output', type=str, required=True, help='Output parquet file')
    parser.add_argument('--score-columns', type=str, nargs='+', 
                        default=['Alignment', 'Realism', 'Aesthetics', 'Plausibility'],
                        help='Teacher score dimension columns')
    return parser.parse_args()

def main():
    """Main entry point."""
    logger = setup_logging()
    args = parse_args()
    
    try:
        integrate_features(args.input, args.output, args.score_columns)
    except Exception as e:
        logger.error(f"Integration failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
