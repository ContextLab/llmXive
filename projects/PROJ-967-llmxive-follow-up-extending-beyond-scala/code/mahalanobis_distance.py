import argparse
import json
import logging
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def setup_directories(base_path):
    """Ensure necessary directories exist."""
    processed_dir = base_path / 'data' / 'processed'
    results_dir = base_path / 'results'
    processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir, results_dir

def load_model_selection(base_path):
    """Load model selection JSON to determine if RF was used."""
    model_sel_path = base_path / 'data' / 'processed' / 'model_selection.json'
    if not model_sel_path.exists():
        raise FileNotFoundError(f"Model selection file not found: {model_sel_path}")
    
    with open(model_sel_path, 'r') as f:
        return json.load(f)

def load_covariance_matrix(base_path):
    """Load the global covariance matrix from results."""
    cov_path = base_path / 'results' / 'covariance_matrix.json'
    if not cov_path.exists():
        raise FileNotFoundError(f"Covariance matrix file not found: {cov_path}")
    
    with open(cov_path, 'r') as f:
        data = json.load(f)
    
    # Handle case where data might be a dict with a 'matrix' key or just the list
    if isinstance(data, dict) and 'matrix' in data:
        return np.array(data['matrix'])
    return np.array(data)

def load_global_mean(base_path):
    """Load the global mean vector from results."""
    mean_path = base_path / 'results' / 'global_mean.json'
    if not mean_path.exists():
        # Fallback: try to infer from covariance file if mean isn't saved separately
        # But per spec, we expect a saved mean. If missing, we might need to compute it.
        # However, T022b usually saves mean. Let's check if we have a fallback mechanism.
        # For robustness, if the file is missing, we can't proceed without the mean.
        raise FileNotFoundError(f"Global mean file not found: {mean_path}")
    
    with open(mean_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'mean' in data:
        return np.array(data['mean'])
    return np.array(data)

def load_cleaned_data(base_path):
    """Load the filtered cleaned dataset."""
    data_path = base_path / 'data' / 'processed' / 'cleaned_data.parquet'
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {data_path}")
    
    return pd.read_parquet(data_path)

def calculate_mahalanobis_distance(df, cov_matrix, mean_vector, logger):
    """
    Calculate Mahalanobis distance for each sample.
    D_M(x) = sqrt((x - mu)^T * Sigma^-1 * (x - mu))
    
    Handles singular matrices by using pseudo-inverse.
    """
    # Extract teacher scores columns (assuming they are named Alignment, Realism, Aesthetics, Plausibility)
    # Or based on the schema: teacher_scores object properties.
    # In the dataframe, these are likely expanded columns or a nested structure.
    # Assuming they are expanded columns based on T012/T022a context.
    # If they are nested, we need to explode. Let's assume expanded columns for now:
    # 'Alignment', 'Realism', 'Aesthetics', 'Plausibility'
    
    dimension_cols = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
    
    # Check if columns exist
    missing_cols = [col for col in dimension_cols if col not in df.columns]
    if missing_cols:
        # Try to find them in a nested structure if necessary, but spec implies flat for calculation
        # If they are in a 'teacher_scores' column as dict, we need to normalize first.
        # Given T022a output 'entanglement_scores.csv', let's assume the input df has these columns.
        # If not, we raise an error.
        raise ValueError(f"Missing required dimension columns: {missing_cols}")
    
    X = df[dimension_cols].values.astype(float)
    
    # Center the data
    X_centered = X - mean_vector
    
    # Calculate pseudo-inverse of covariance matrix
    try:
        cov_inv = np.linalg.inv(cov_matrix)
    except np.linalg.LinAlgError:
        logger.warning("Covariance matrix is singular. Using pseudo-inverse.")
        cov_inv = np.linalg.pinv(cov_matrix)
    
    # Calculate Mahalanobis distance
    # D = sqrt( (X-mu) * Sigma^-1 * (X-mu)^T )
    # Vectorized: sum over axis 1 of (X_centered @ cov_inv * X_centered)
    diff = X_centered
    # (N, 4) @ (4, 4) -> (N, 4)
    left = diff @ cov_inv
    # (N, 4) * (N, 4) -> (N, 4) then sum
    mahal_sq = np.sum(left * diff, axis=1)
    
    # Ensure non-negative (numerical errors can cause tiny negatives)
    mahal_sq = np.maximum(mahal_sq, 0)
    mahal_dist = np.sqrt(mahal_sq)
    
    return mahal_dist

def save_results(df, mahal_dist, base_path, logger):
    """Save the updated dataframe with Mahalanobis distance."""
    df['mahalanobis_distance'] = mahal_dist
    
    output_path = base_path / 'data' / 'processed' / 'entanglement_scores.csv'
    df.to_csv(output_path, index=False)
    logger.info(f"Saved entanglement scores with Mahalanobis distance to {output_path}")
    
    # Also save a status log
    status = {
        "task": "T022c",
        "status": "completed",
        "output_file": str(output_path),
        "count": len(df),
        "mean_mahalanobis": float(np.mean(mahal_dist)),
        "std_mahalanobis": float(np.std(mahal_dist))
    }
    
    status_path = base_path / 'data' / 'processed' / 'feature_status.json'
    with open(status_path, 'w') as f:
        json.dump(status, f, indent=2)
    logger.info(f"Saved feature status to {status_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Calculate Per-Sample Mahalanobis Distance")
    parser.add_argument('--base-path', type=str, default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala',
                        help='Base path of the project')
    return parser.parse_args()

def main():
    args = parse_args()
    base_path = Path(args.base_path)
    logger = setup_logging()
    
    # 1. Check Model Selection
    logger.info("Loading model selection...")
    model_selection = load_model_selection(base_path)
    model_type = model_selection.get('model_type', 'unknown')
    
    if model_type != 'rf':
        logger.warning(f"Model type is '{model_type}', not 'rf'. Skipping Mahalanobis calculation.")
        status = {
            "task": "T022c",
            "status": "skipped",
            "reason": f"Model type is '{model_type}', not 'rf'"
        }
        status_path = base_path / 'data' / 'processed' / 'feature_status.json'
        with open(status_path, 'w') as f:
            json.dump(status, f, indent=2)
        return
    
    logger.info(f"Model type is 'rf'. Proceeding with Mahalanobis calculation.")
    
    # 2. Load Global Covariance and Mean
    logger.info("Loading global covariance matrix and mean...")
    try:
        cov_matrix = load_covariance_matrix(base_path)
        mean_vector = load_global_mean(base_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 3. Load Cleaned Data
    logger.info("Loading cleaned data...")
    try:
        df = load_cleaned_data(base_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    if df.empty:
        logger.warning("Cleaned data is empty. Nothing to process.")
        return
    
    # 4. Calculate Mahalanobis Distance
    logger.info("Calculating Mahalanobis distance...")
    mahal_dist = calculate_mahalanobis_distance(df, cov_matrix, mean_vector, logger)
    
    # 5. Save Results
    save_results(df, mahal_dist, base_path, logger)
    
    logger.info("Task T022c completed successfully.")

if __name__ == "__main__":
    main()
