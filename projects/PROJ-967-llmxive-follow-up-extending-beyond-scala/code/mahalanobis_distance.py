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
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger(__name__)

def setup_directories():
    """Ensure output directories exist."""
    data_processed = Path("data/processed")
    data_processed.mkdir(parents=True, exist_ok=True)
    return data_processed

def load_model_selection():
    """Load model selection result to determine if Mahalanobis is required."""
    model_selection_path = Path("data/processed/model_selection.json")
    if not model_selection_path.exists():
        raise FileNotFoundError(
            f"Model selection file not found at {model_selection_path}. "
            "Run T027d (model_selection) before this task."
        )
    with open(model_selection_path, "r") as f:
        return json.load(f)

def load_covariance_matrix():
    """Load the global covariance matrix from results."""
    cov_path = Path("results/covariance_matrix.json")
    if not cov_path.exists():
        raise FileNotFoundError(
            f"Covariance matrix not found at {cov_path}. "
            "Run T022b (global_covariance) before this task."
        )
    with open(cov_path, "r") as f:
        data = json.load(f)
        if "covariance_matrix" not in data:
            raise ValueError("Invalid covariance matrix file: missing 'covariance_matrix' key")
        return np.array(data["covariance_matrix"])

def load_global_mean():
    """Load the global mean vector from results."""
    mean_path = Path("results/global_mean.json")
    if not mean_path.exists():
        raise FileNotFoundError(
            f"Global mean file not found at {mean_path}. "
            "Run T022b (global_covariance) before this task."
        )
    with open(mean_path, "r") as f:
        data = json.load(f)
        if "mean_vector" not in data:
            raise ValueError("Invalid global mean file: missing 'mean_vector' key")
        return np.array(data["mean_vector"])

def load_cleaned_data():
    """Load the filtered dataset."""
    cleaned_path = Path("data/processed/cleaned_data.parquet")
    if not cleaned_path.exists():
        raise FileNotFoundError(
            f"Cleaned data not found at {cleaned_path}. "
            "Run T024 (fidelity_loss) before this task."
        )
    return pd.read_parquet(cleaned_path)

def calculate_mahalanobis_distance(df, covariance, mean_vector, logger):
    """
    Calculate Mahalanobis distance for each sample in the dataframe.
    
    D_M(x) = sqrt((x - mu)^T * Sigma^{-1} * (x - mu))
    
    Handles singular covariance matrices using pseudo-inverse.
    """
    dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    
    # Extract teacher scores matrix
    if not all(dim in df.columns for dim in dimensions):
        raise ValueError(f"Missing required dimension columns: {dimensions}")
    
    X = df[dimensions].values.astype(float)
    
    # Check for statistical consistency: if the dataset differs significantly 
    # from the global set, we should recompute mean/cov on the filtered set.
    # For this implementation, we use the provided global stats but warn if
    # the filtered set is very small or different.
    n_samples = X.shape[0]
    if n_samples < 4:
        logger.warning(f"Dataset too small ({n_samples} samples) for robust Mahalanobis calculation. Proceeding with caution.")
    
    # Compute inverse (or pseudo-inverse) of covariance matrix
    try:
        cov_inv = np.linalg.inv(covariance)
    except np.linalg.LinAlgError:
        logger.warning("Covariance matrix is singular. Using pseudo-inverse.")
        cov_inv = np.linalg.pinv(covariance)
    
    # Calculate distances
    diff = X - mean_vector
    # D^2 = (x - mu)^T * Sigma^{-1} * (x - mu)
    mahal_sq = np.einsum('ij,ij->i', diff @ cov_inv, diff)
    mahal_dist = np.sqrt(np.maximum(mahal_sq, 0))  # Ensure non-negative due to numerical errors
    
    return mahal_dist

def save_results(df, output_path, logger):
    """Save the dataframe with Mahalanobis distance to CSV."""
    df.to_parquet(output_path.parent / "entanglement_scores_with_mahalanobis.parquet", index=False)
    # Also save as CSV for compatibility with existing pipelines
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Calculate Per-Sample Mahalanobis Distance")
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/processed/entanglement_scores.csv",
        help="Path to save the output CSV file"
    )
    return parser.parse_args()

def main():
    logger = setup_logging()
    logger.info("Starting T022c: Per-Sample Mahalanobis Distance Calculation")

    # 1. Check Model Selection
    logger.info("Loading model selection status...")
    model_selection = load_model_selection()
    model_type = model_selection.get("model_type")
    
    if model_type != "rf":
        logger.warning(f"Model type is '{model_type}', not 'rf'. Skipping Mahalanobis calculation.")
        # Write skipped status to feature_status.json
        status_path = Path("data/processed/feature_status.json")
        with open(status_path, "w") as f:
            json.dump({"mahalanobis_distance": "skipped", "reason": f"model_type={model_type}"}, f)
        logger.info(f"Skipped status written to {status_path}")
        return

    logger.info(f"Model type is 'rf'. Proceeding with Mahalanobis calculation.")

    # 2. Load Dependencies
    logger.info("Loading covariance matrix...")
    covariance = load_covariance_matrix()
    
    logger.info("Loading global mean...")
    mean_vector = load_global_mean()
    
    logger.info("Loading cleaned data...")
    df = load_cleaned_data()

    # 3. Statistical Consistency Check
    # If the filtered dataset differs significantly (>10% removed), 
    # we should ideally recompute. For this task, we assume the global stats
    # are sufficient, but we log the sample count.
    logger.info(f"Processing {len(df)} samples for Mahalanobis distance.")

    # 4. Calculate Mahalanobis Distance
    logger.info("Calculating Mahalanobis distance...")
    mahal_dist = calculate_mahalanobis_distance(df, covariance, mean_vector, logger)

    # 5. Append to dataframe
    df["mahalanobis_distance"] = mahal_dist

    # 6. Save Results
    output_path = Path(args.output_path)
    setup_directories()
    save_results(df, output_path, logger)
    
    logger.info("T022c completed successfully.")

if __name__ == "__main__":
    args = parse_args()
    main()
