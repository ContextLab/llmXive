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
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Compute global covariance matrix and dominant eigenvalue from filtered dataset."
    )
    parser.add_argument(
        "--input-path",
        type=str,
        default="data/processed/cleaned_data.parquet",
        help="Path to the filtered dataset (output of T024)."
    )
    parser.add_argument(
        "--output-covariance",
        type=str,
        default="results/covariance_matrix.json",
        help="Path to save the covariance matrix JSON."
    )
    parser.add_argument(
        "--output-eigenvalue",
        type=str,
        default="results/dominant_eigenvalue.json",
        help="Path to save the dominant eigenvalue JSON."
    )
    return parser.parse_args()

def load_cleaned_data(input_path: str, logger: logging.Logger) -> pd.DataFrame:
    """Load the filtered dataset from parquet."""
    logger.info(f"Loading cleaned data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def extract_teacher_scores_matrix(df: pd.DataFrame, logger: logging.Logger) -> np.ndarray:
    """
    Extract the N x 4 matrix of teacher scores.
    Expects columns: Alignment, Realism, Aesthetics, Plausibility.
    """
    required_cols = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise RuntimeError(f"Missing required teacher score columns: {missing_cols}")

    matrix = df[required_cols].to_numpy(dtype=np.float64)
    logger.info(f"Extracted teacher scores matrix: {matrix.shape}")
    return matrix

def calculate_global_covariance_and_eigenvalue(matrix: np.ndarray, logger: logging.Logger):
    """
    Compute the 4x4 covariance matrix and the dominant (largest) eigenvalue.
    Returns (cov_matrix, dominant_eigenvalue).
    """
    n_samples, n_dims = matrix.shape
    if n_samples < 4:
        raise RuntimeError(
            f"Insufficient samples for covariance estimation: N={n_samples}. "
            "Requires at least 4 samples to compute a 4x4 covariance matrix."
        )

    # Compute covariance matrix (rowvar=False means columns are variables)
    cov_matrix = np.cov(matrix, rowvar=False)
    logger.info(f"Computed covariance matrix: {cov_matrix.shape}")

    # Compute eigenvalues
    eigenvalues, _ = np.linalg.eigh(cov_matrix)
    dominant_eigenvalue = float(np.max(eigenvalues))
    logger.info(f"Dominant eigenvalue: {dominant_eigenvalue}")

    return cov_matrix, dominant_eigenvalue

def save_covariance_matrix(cov_matrix: np.ndarray, output_path: str, logger: logging.Logger):
    """Save the covariance matrix to a JSON file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "shape": list(cov_matrix.shape),
        "values": cov_matrix.tolist()
    }
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Covariance matrix saved to {output_path}")

def save_dominant_eigenvalue(eigenvalue: float, output_path: str, logger: logging.Logger):
    """Save the dominant eigenvalue to a JSON file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "dominant_eigenvalue": eigenvalue
    }
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Dominant eigenvalue saved to {output_path}")

def main():
    """Main entry point for T022b."""
    logger = setup_logging()
    args = parse_args()

    logger.info("Starting Global Covariance Matrix computation (T022b)")

    # 1. Load filtered data
    df = load_cleaned_data(args.input_path, logger)

    # 2. Extract teacher scores
    matrix = extract_teacher_scores_matrix(df, logger)

    # 3. Compute covariance and eigenvalue
    cov_matrix, dominant_eig = calculate_global_covariance_and_eigenvalue(matrix, logger)

    # 4. Save outputs
    save_covariance_matrix(cov_matrix, args.output_covariance, logger)
    save_dominant_eigenvalue(dominant_eig, args.output_eigenvalue, logger)

    logger.info("T022b completed successfully")

if __name__ == "__main__":
    main()
