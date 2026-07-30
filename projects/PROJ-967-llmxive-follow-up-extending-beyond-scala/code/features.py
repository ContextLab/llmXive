"""
Feature engineering module for llmXive entanglement analysis.
Implements statistical descriptors and global covariance metrics.
"""
import argparse
import json
import logging
import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for the module."""
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def setup_directories(base_path: str) -> Dict[str, Path]:
    """Ensure required directories exist."""
    base = Path(base_path)
    dirs = {
        'raw': base / 'data' / 'raw',
        'processed': base / 'data' / 'processed',
        'results': base / 'results',
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs

def load_raw_dataset(raw_dir: Path) -> pd.DataFrame:
    """
    Load the raw dataset from the data/raw directory.
    T037 ensures this file exists. We look for the parquet file.
    """
    parquet_files = list(raw_dir.glob("*.parquet"))
    if not parquet_files:
        # Fallback to CSV if parquet not found, though T037/T012 should produce parquet
        csv_files = list(raw_dir.glob("*.csv"))
        if csv_files:
            return pd.read_csv(csv_files[0])
        raise FileNotFoundError(f"No dataset found in {raw_dir}")

    # Prefer the most recently modified or the first one
    data_path = parquet_files[0]
    logger.info(f"Loading raw dataset from: {data_path}")
    return pd.read_parquet(data_path)

def extract_teacher_scores_matrix(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    """
    Extract the N x 4 matrix of teacher scores.
    Handles nested dictionary columns if present.
    """
    # Identify the column containing teacher scores
    # Based on schema: 'teacher_scores' is a dict/object column
    score_col = None
    for col in df.columns:
        if 'teacher' in col.lower() and 'score' in col.lower():
            score_col = col
            break

    if score_col is None:
        raise ValueError("Could not find 'teacher_scores' column in dataset.")

    # Extract the scores
    scores_list = []
    valid_indices = []
    required_dims = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']

    for idx, row in df.iterrows():
        scores = row[score_col]
        if pd.isna(scores):
            continue

        # Handle if scores is a string representation of a dict
        if isinstance(scores, str):
            try:
                scores = json.loads(scores)
            except json.JSONDecodeError:
                continue

        if not isinstance(scores, dict):
            continue

        # Extract values in specific order
        try:
            vec = [float(scores[d]) for d in required_dims]
            if any(math.isnan(v) for v in vec):
                continue
            scores_list.append(vec)
            valid_indices.append(idx)
        except (KeyError, TypeError, ValueError):
            # Missing a dimension, skip this sample for global covariance
            continue

    if len(scores_list) == 0:
        raise RuntimeError("No valid teacher score vectors found for covariance calculation.")

    logger.info(f"Extracted {len(scores_list)} valid teacher score vectors from {len(df)} rows.")
    return np.array(scores_list), required_dims

def calculate_global_covariance_and_eigenvalue(scores_matrix: np.ndarray) -> Dict[str, Any]:
    """
    Calculate the Global Covariance Matrix and Dominant Eigenvalue.
    Input: N x 4 matrix of teacher scores.
    Output: Dictionary containing covariance matrix, eigenvalues, eigenvectors, and dominant eigenvalue.
    """
    # Compute covariance matrix (4x4)
    # rowvar=False indicates that columns are features (dimensions)
    cov_matrix = np.cov(scores_matrix, rowvar=False)

    if np.any(np.isnan(cov_matrix)):
        logger.warning("Covariance matrix contains NaN. Attempting to handle.")
        # If NaN, it might be due to constant columns or insufficient data
        # We will raise an error here as per strict requirements, but log context
        raise RuntimeError("Covariance matrix contains NaN values. Check data quality.")

    # Calculate eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)

    # Sort eigenvalues and eigenvectors in descending order
    sorted_indices = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[sorted_indices]
    eigenvectors = eigenvectors[:, sorted_indices]

    dominant_eigenvalue = float(eigenvalues[0])

    result = {
        "covariance_matrix": cov_matrix.tolist(),
        "eigenvalues": eigenvalues.tolist(),
        "dominant_eigenvalue": dominant_eigenvalue,
        "eigenvectors": eigenvectors.tolist(),
        "num_samples": scores_matrix.shape[0],
        "dimensions": 4
    }

    logger.info(f"Global Covariance calculated. Dominant Eigenvalue: {dominant_eigenvalue:.6f}")
    return result

def save_global_stats(stats: Dict[str, Any], output_path: Path) -> None:
    """Save global statistics to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Global statistics saved to: {output_path}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculate Global Covariance and Dominant Eigenvalue")
    parser.add_argument('--base_path', type=str, default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala',
                        help='Base path of the project')
    parser.add_argument('--output_file', type=str, default='global_covariance_stats.json',
                        help='Output filename for global stats')
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    base_path = Path(args.base_path)
    setup_logging()

    # Setup directories
    dirs = setup_directories(base_path)

    # 1. Load raw dataset (from T037 output)
    try:
        df = load_raw_dataset(dirs['raw'])
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # 2. Extract teacher scores matrix
    try:
        scores_matrix, dims = extract_teacher_scores_matrix(df)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # 3. Calculate Global Covariance and Dominant Eigenvalue
    try:
        global_stats = calculate_global_covariance_and_eigenvalue(scores_matrix)
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)

    # 4. Save output
    output_path = dirs['processed'] / args.output_file
    save_global_stats(global_stats, output_path)

    # Print summary to stdout for verification
    print(json.dumps({
        "status": "success",
        "dominant_eigenvalue": global_stats["dominant_eigenvalue"],
        "num_samples_used": global_stats["num_samples"]
    }, indent=2))

if __name__ == "__main__":
    main()
