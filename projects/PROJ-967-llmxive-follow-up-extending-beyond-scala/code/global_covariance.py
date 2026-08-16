"""
Global Covariance Matrix and Dominant Eigenvalue Calculation.

Computes the 4x4 covariance matrix of teacher scores across the entire
aligned dataset (before filtering) and extracts the dominant eigenvalue.

Outputs:
    results/covariance_matrix.json: The 4x4 covariance matrix.
    results/dominant_eigenvalue.json: The largest eigenvalue.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

def setup_logging():
    """Configure basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Compute global covariance matrix and dominant eigenvalue."
    )
    parser.add_argument(
        "--input-path",
        type=str,
        default="data/processed/raw_data.parquet",
        help="Path to the raw aligned dataset (parquet).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory to write output JSON files.",
    )
    return parser.parse_args()

def calculate_global_covariance_and_eigenvalue(df: pd.DataFrame, logger: logging.Logger) -> tuple:
    """
    Extract the N x 4 matrix of teacher scores and compute covariance/eigenvalue.
    
    Args:
        df: DataFrame containing teacher scores.
        logger: Logger instance.
        
    Returns:
        tuple: (covariance_matrix (np.array), dominant_eigenvalue (float))
        
    Raises:
        RuntimeError: If N < 4 or columns are missing.
    """
    required_dims = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    
    # Check for missing columns
    missing_cols = [col for col in required_dims if col not in df.columns]
    if missing_cols:
        raise RuntimeError(f"Missing required teacher score columns: {missing_cols}")
    
    # Extract the matrix
    teacher_matrix = df[required_dims].to_numpy()
    n_samples = teacher_matrix.shape[0]
    
    logger.info(f"Extracted teacher scores matrix: {n_samples} samples x 4 dimensions.")
    
    if n_samples < 4:
        raise RuntimeError(
            f"Insufficient data points for covariance calculation. "
            f"Need at least 4 samples, got {n_samples}."
        )
    
    # Compute covariance matrix (rowvar=False means columns are variables)
    # numpy.cov returns a float64 array
    cov_matrix = np.cov(teacher_matrix, rowvar=False)
    
    if cov_matrix.ndim != 2 or cov_matrix.shape != (4, 4):
        raise RuntimeError(f"Unexpected covariance matrix shape: {cov_matrix.shape}")
    
    # Compute eigenvalues
    eigenvalues = np.linalg.eigvalsh(cov_matrix) # eigvalsh for symmetric matrices
    
    if len(eigenvalues) != 4:
        raise RuntimeError(f"Unexpected number of eigenvalues: {len(eigenvalues)}")
    
    dominant_eigenvalue = float(np.max(eigenvalues))
    
    logger.info(f"Covariance matrix computed successfully.")
    logger.info(f"Dominant eigenvalue: {dominant_eigenvalue:.6f}")
    
    return cov_matrix, dominant_eigenvalue

def save_covariance_matrix(cov_matrix: np.ndarray, output_path: Path, logger: logging.Logger):
    """Save covariance matrix to JSON."""
    # Convert numpy array to list of lists for JSON serialization
    matrix_list = cov_matrix.tolist()
    
    with open(output_path, "w") as f:
        json.dump(matrix_list, f, indent=2)
    
    logger.info(f"Covariance matrix saved to {output_path}")

def save_dominant_eigenvalue(eigenvalue: float, output_path: Path, logger: logging.Logger):
    """Save dominant eigenvalue to JSON."""
    with open(output_path, "w") as f:
        json.dump({"dominant_eigenvalue": eigenvalue}, f, indent=2)
    
    logger.info(f"Dominant eigenvalue saved to {output_path}")

def main():
    """Main entry point."""
    args = parse_args()
    logger = setup_logging()
    
    input_path = Path(args.input_path)
    output_dir = Path(args.output_dir)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            f"Please ensure T012 (ingest) has run successfully."
        )
    
    logger.info(f"Loading data from {input_path}...")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load parquet file: {e}")
    
    logger.info(f"Loaded {len(df)} rows.")
    
    cov_matrix, dominant_eigenvalue = calculate_global_covariance_and_eigenvalue(df, logger)
    
    cov_output_path = output_dir / "covariance_matrix.json"
    eigen_output_path = output_dir / "dominant_eigenvalue.json"
    
    save_covariance_matrix(cov_matrix, cov_output_path, logger)
    save_dominant_eigenvalue(dominant_eigenvalue, eigen_output_path, logger)
    
    logger.info("Task T022b completed successfully.")

if __name__ == "__main__":
    main()
