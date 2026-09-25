import os
import sys
import json
import logging
import argparse
from pathlib import Path
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/baseline_computation.log')
    ]
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

def load_filtered_data():
    """Load the filtered training and test data."""
    train_path = DATA_PROCESSED / "filtered_train.csv"
    test_path = DATA_PROCESSED / "filtered_test.csv"
    
    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError("Filtered data files not found. Run T030.1 first.")
    
    import pandas as pd
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    
    return train_df, test_df

def compute_baseline_distribution(train_df, test_df):
    """Compute baseline distribution statistics from filtered data."""
    logger.info("Computing baseline distribution statistics...")
    
    # Load features
    features_path = DATA_PROCESSED / "features.npy"
    if not features_path.exists():
        raise FileNotFoundError(f"Features file not found: {features_path}")
    
    features = np.load(features_path)
    logger.info(f"Loaded features with shape: {features.shape}")
    
    # Align features with labels (assuming order matches CSV)
    # We need to map clip_ids to indices if necessary, but for simplicity assume order
    # In a real scenario, we would join on clip_id
    
    # Compute statistics for activation vectors (first N columns if features are flattened)
    # Assuming features are [N_samples, N_features]
    mean_activation = np.mean(features, axis=0)
    std_activation = np.std(features, axis=0)
    
    # Histogram of activations (bin counts)
    hist, bin_edges = np.histogram(features, bins=50)
    
    # Expert mask counts (assuming last few columns are masks)
    # For this example, we assume the last 10 columns are masks if they exist
    n_features = features.shape[1]
    mask_cols = slice(max(0, n_features - 10), n_features)
    expert_mask_counts = np.sum(features[:, mask_cols] > 0.5, axis=0)
    
    baseline_distribution = {
        "mean_activation": mean_activation.tolist(),
        "std_activation": std_activation.tolist(),
        "histogram": {
            "counts": hist.tolist(),
            "bin_edges": bin_edges.tolist()
        },
        "expert_mask_counts": expert_mask_counts.tolist(),
        "n_samples_train": len(train_df),
        "n_samples_test": len(test_df)
    }
    
    return baseline_distribution

def save_baseline_distribution(baseline_distribution, output_path):
    """Save baseline distribution to JSON."""
    with open(output_path, 'w') as f:
        json.dump(baseline_distribution, f, indent=2)
    logger.info(f"Baseline distribution saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Compute baseline distribution for activation vectors.")
    args = parser.parse_args()
    
    try:
        train_df, test_df = load_filtered_data()
        baseline_dist = compute_baseline_distribution(train_df, test_df)
        output_path = DATA_PROCESSED / "activation_distribution.json"
        save_baseline_distribution(baseline_dist, output_path)
    except Exception as e:
        logger.error(f"Baseline computation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()