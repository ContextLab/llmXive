"""
Entanglement Scores Module
Computes per-sample entanglement features (variance, entropy, skewness, kurtosis)
from teacher scores and integrates them into the features dataset.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import entropy, skew, kurtosis

# --- Logging Setup ---
def setup_logging(log_file: str = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
    return logger

# --- Data Loading ---
def load_cleaned_data(path: str) -> pd.DataFrame:
    """Load the cleaned dataset from parquet."""
    logger = logging.getLogger(__name__)
    if not os.path.exists(path):
        logger.error(f"Cleaned data file not found: {path}")
        raise FileNotFoundError(f"Cleaned data file not found: {path}")
    logger.info(f"Loading cleaned data from {path}")
    return pd.read_parquet(path)

def load_dominant_eigenvalue(path: str) -> float:
    """Load the dominant eigenvalue from JSON."""
    logger = logging.getLogger(__name__)
    if not os.path.exists(path):
        logger.error(f"Dominant eigenvalue file not found: {path}")
        raise FileNotFoundError(f"Dominant eigenvalue file not found: {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    return float(data['dominant_eigenvalue'])

def load_covariance_matrix(path: str) -> np.ndarray:
    """Load the covariance matrix from JSON."""
    logger = logging.getLogger(__name__)
    if not os.path.exists(path):
        logger.error(f"Covariance matrix file not found: {path}")
        raise FileNotFoundError(f"Covariance matrix file not found: {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    return np.array(data['covariance_matrix'])

# --- Feature Computation ---
def extract_teacher_scores_matrix(df: pd.DataFrame) -> np.ndarray:
    """Extract the teacher scores matrix from the dataframe."""
    # Assuming columns are named 'teacher_dim_0', 'teacher_dim_1', etc.
    # or a list of columns starting with 'teacher_'
    cols = [c for c in df.columns if c.startswith('teacher_dim_')]
    if not cols:
        # Fallback to generic teacher_ prefix if specific naming differs
        cols = [c for c in df.columns if c.startswith('teacher_')]
    
    if len(cols) == 0:
        raise ValueError("No teacher score columns found in the dataset.")
    
    # Sort columns to ensure consistent order
    cols.sort()
    return df[cols].values

def compute_per_sample_stats(teacher_matrix: np.ndarray) -> dict:
    """
    Compute variance, entropy, skewness, and kurtosis for each sample (row).
    Returns a dictionary with lists of values for each metric.
    """
    n_samples = teacher_matrix.shape[0]
    n_dims = teacher_matrix.shape[1]
    
    variances = []
    entropies = []
    skewnesses = []
    kurtosises = []
    
    for i in range(n_samples):
        scores = teacher_matrix[i, :]
        
        # Variance
        var = np.var(scores)
        variances.append(var)
        
        # Entropy (using Gaussian assumption for continuous data or discretization)
        # For continuous data, differential entropy is often used.
        # Here we use a simple histogram-based entropy for robustness across scales.
        # Or, if we assume the scores are normalized probabilities, we use standard entropy.
        # Given the context of "rubric dimensions", scores might be arbitrary.
        # Let's use a robust approach: normalize to positive and sum to 1 for entropy calculation
        # or use Gaussian differential entropy: 0.5 * log(2 * pi * e * var)
        
        # Approach: Gaussian Differential Entropy (more stable for continuous scores)
        if var > 0:
            diff_entropy = 0.5 * np.log(2 * np.pi * np.e * var)
        else:
            diff_entropy = -np.inf # Or 0 depending on convention
        entropies.append(diff_entropy)
        
        # Skewness
        sk = skew(scores, nan_policy='omit')
        skewnesses.append(sk)
        
        # Kurtosis (Fisher's definition, normal=0)
        ku = kurtosis(scores, nan_policy='omit', fisher=True)
        kurtosises.append(ku)
    
    return {
        'variance': variances,
        'entropy': entropies,
        'skewness': skewnesses,
        'kurtosis': kurtosises
    }

def compute_mahalanobis_distance(teacher_matrix: np.ndarray, 
                                 covariance_matrix: np.ndarray, 
                                 mean_vector: np.ndarray) -> np.ndarray:
    """
    Compute Mahalanobis distance for each sample.
    Handles singular matrices by using pseudo-inverse.
    """
    # Covariance matrix might be singular; use pseudo-inverse
    try:
        cov_inv = np.linalg.inv(covariance_matrix)
    except np.linalg.LinAlgError:
        logging.getLogger(__name__).warning("Covariance matrix is singular. Using pseudo-inverse.")
        cov_inv = np.linalg.pinv(covariance_matrix, rcond=1e-15)
    
    diff = teacher_matrix - mean_vector
    # Mahalanobis: sqrt((x-mu)^T * Sigma^-1 * (x-mu))
    # Vectorized: sqrt(sum over dims of (diff @ cov_inv) * diff)
    mahal_sq = np.sum(diff @ cov_inv * diff, axis=1)
    # Avoid negative zeros due to floating point errors
    mahal_sq = np.maximum(mahal_sq, 0)
    return np.sqrt(mahal_sq)

# --- Integration & Saving ---
def integrate_features(df: pd.DataFrame, stats: dict, mahalanobis_distances: np.ndarray, 
                       global_eigenvalue: float) -> pd.DataFrame:
    """Integrate computed stats and Mahalanobis distance into the dataframe."""
    df['variance'] = stats['variance']
    df['entropy'] = stats['entropy']
    df['skewness'] = stats['skewness']
    df['kurtosis'] = stats['kurtosis']
    df['mahalanobis_distance'] = mahalanobis_distances
    df['global_eigenvalue'] = global_eigenvalue
    return df

def save_features(df: pd.DataFrame, output_path: str):
    """Save the enriched dataframe to a JSON file (or parquet if preferred, but task says features.json)."""
    logger = logging.getLogger(__name__)
    # Convert to list of dicts for JSON serialization
    # Ensure numpy types are converted to python native types
    records = df.to_dict(orient='records')
    # Handle numpy types conversion
    for record in records:
        for key, value in record.items():
            if isinstance(value, (np.integer, np.floating)):
                record[key] = float(value)
            elif isinstance(value, (np.ndarray,)):
                record[key] = value.tolist()
    
    with open(output_path, 'w') as f:
        json.dump(records, f, indent=2)
    logger.info(f"Features saved to {output_path}")

# --- CLI ---
def parse_args():
    parser = argparse.ArgumentParser(description="Compute and save per-sample entanglement features.")
    parser.add_argument("--input-path", type=str, default="data/processed/cleaned_data.parquet",
                        help="Path to the cleaned data parquet file.")
    parser.add_argument("--covariance-path", type=str, default="results/covariance_matrix.json",
                        help="Path to the covariance matrix JSON file.")
    parser.add_argument("--eigenvalue-path", type=str, default="results/dominant_eigenvalue.json",
                        help="Path to the dominant eigenvalue JSON file.")
    parser.add_argument("--output-path", type=str, default="data/processed/features.json",
                        help="Path to save the output features JSON file.")
    parser.add_argument("--log-file", type=str, default=None,
                        help="Path to save the log file.")
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging(args.log_file)
    
    try:
        # Load Data
        df = load_cleaned_data(args.input_path)
        cov_matrix = load_covariance_matrix(args.covariance_path)
        eigenvalue = load_dominant_eigenvalue(args.eigenvalue_path)
        
        # Compute Global Mean for Mahalanobis
        teacher_matrix = extract_teacher_scores_matrix(df)
        global_mean = np.mean(teacher_matrix, axis=0)
        
        # Compute Per-Sample Stats
        stats = compute_per_sample_stats(teacher_matrix)
        
        # Compute Mahalanobis Distance
        mahalanobis_distances = compute_mahalanobis_distance(teacher_matrix, cov_matrix, global_mean)
        
        # Integrate
        df_enriched = integrate_features(df, stats, mahalanobis_distances, eigenvalue)
        
        # Save
        save_features(df_enriched, args.output_path)
        
        logger.info("Task T022a completed successfully.")
        
    except Exception as e:
        logger.error(f"Task T022a failed: {e}")
        raise

if __name__ == "__main__":
    main()
