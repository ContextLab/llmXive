import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.distance import mahalanobis

def setup_logging():
    """Configure logging for the Mahalanobis distance calculation task."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('results/mahalanobis_distance.log')
        ]
    )
    return logging.getLogger(__name__)

def setup_directories(base_dir: Path):
    """Ensure required output directories exist."""
    (base_dir / 'data' / 'processed').mkdir(parents=True, exist_ok=True)
    (base_dir / 'results').mkdir(parents=True, exist_ok=True)

def load_model_selection(base_dir: Path):
    """Load the model selection JSON to determine execution context."""
    path = base_dir / 'data' / 'processed' / 'model_selection.json'
    if not path.exists():
        raise FileNotFoundError(f"Model selection file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_covariance_matrix(base_dir: Path):
    """Load the global covariance matrix computed in T022b-filtered."""
    path = base_dir / 'results' / 'covariance_matrix.json'
    if not path.exists():
        raise FileNotFoundError(f"Covariance matrix file not found: {path}")
    with open(path, 'r') as f:
        data = json.load(f)
        return np.array(data['covariance_matrix'])

def load_global_mean(base_dir: Path):
    """Load the global mean vector computed in T022b-filtered."""
    path = base_dir / 'results' / 'global_mean.json'
    if not path.exists():
        raise FileNotFoundError(f"Global mean file not found: {path}")
    with open(path, 'r') as f:
        data = json.load(f)
        return np.array(data['mean_vector'])

def load_cleaned_data(base_dir: Path):
    """Load the filtered dataset from T024."""
    path = base_dir / 'data' / 'processed' / 'cleaned_data.parquet'
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {path}")
    return pd.read_parquet(path)

def calculate_mahalanobis_distance(df: pd.DataFrame, cov_matrix: np.ndarray, mean_vector: np.ndarray, logger: logging.Logger) -> np.ndarray:
    """
    Compute Mahalanobis distance for each sample in the dataframe.

    D_M(x) = sqrt((x - mu)^T * Sigma^-1 * (x - mu))

    Handles singular covariance matrices using pseudo-inverse.
    """
    dimensions = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
    X = df[dimensions].values

    # Ensure dimensions match
    if X.shape[1] != 4 or cov_matrix.shape[0] != 4 or cov_matrix.shape[1] != 4:
        raise ValueError(f"Dimension mismatch: X={X.shape}, cov={cov_matrix.shape}")

    # Check for singularity and use pseudo-inverse if needed
    try:
        cov_inv = np.linalg.inv(cov_matrix)
        logger.info("Covariance matrix is invertible. Using standard inverse.")
    except np.linalg.LinAlgError:
        logger.warning("Covariance matrix is singular. Using pseudo-inverse (rcond=1e-15).")
        cov_inv = np.linalg.pinv(cov_matrix, rcond=1e-15)

    distances = []
    for i, row in enumerate(X):
        diff = row - mean_vector
        dist = np.sqrt(np.dot(np.dot(diff, cov_inv), diff))
        distances.append(dist)

    return np.array(distances)

def save_results(base_dir: Path, df: pd.DataFrame, logger: logging.Logger):
    """Save the updated dataframe with Mahalanobis distance to features.json."""
    output_path = base_dir / 'data' / 'processed' / 'features.json'

    # Load existing features if present (merge with T022a output)
    existing_features = []
    if output_path.exists():
        with open(output_path, 'r') as f:
            existing_features = json.load(f)
            if not isinstance(existing_features, list):
                existing_features = []

    # Convert dataframe to list of dicts
    df_records = df.to_dict('records')

    # Merge: ensure we don't duplicate if 'mahalanobis_distance' already exists
    # (though T022a should not have added it yet)
    merged_features = []
    for record in df_records:
        merged = {k: v for k, v in record.items()}
        merged_features.append(merged)

    # Write output
    with open(output_path, 'w') as f:
        json.dump(merged_features, f, indent=2)

    logger.info(f"Saved {len(merged_features)} records with Mahalanobis distance to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description='Compute Per-Sample Mahalanobis Distance')
    parser.add_argument('--base-dir', type=str, default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala',
                        help='Base directory of the project')
    return parser.parse_args()

def main():
    args = parse_args()
    base_dir = Path(args.base_dir)
    logger = setup_logging()

    logger.info("Starting Mahalanobis Distance calculation (T022c)...")

    # 1. Verify prerequisites
    model_selection = load_model_selection(base_dir)
    logger.info(f"Model selection status: {model_selection.get('model_type', 'unknown')}")

    # 2. Load inputs
    logger.info("Loading cleaned data...")
    df = load_cleaned_data(base_dir)

    logger.info("Loading global covariance matrix...")
    cov_matrix = load_covariance_matrix(base_dir)

    logger.info("Loading global mean vector...")
    mean_vector = load_global_mean(base_dir)

    # 3. Compute Mahalanobis Distance
    logger.info("Computing Mahalanobis distances...")
    distances = calculate_mahalanobis_distance(df, cov_matrix, mean_vector, logger)

    # 4. Append to dataframe
    df['mahalanobis_distance'] = distances

    # 5. Save results
    logger.info("Saving results to features.json...")
    save_results(base_dir, df, logger)

    logger.info("T022c completed successfully.")

if __name__ == '__main__':
    main()
