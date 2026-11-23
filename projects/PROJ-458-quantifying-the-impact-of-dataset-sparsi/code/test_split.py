import os
import sys
import json
import hashlib
import argparse
import pandas as pd
from pathlib import Path

# Ensure project root is in path for imports if running as script
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from utils.logging import get_logger
from utils.checksum_utils import compute_sha256

logger = get_logger(__name__)

RAW_POOL_PATH = Path("data/raw/raw_pool.csv")
TEST_CONFIG_PATH = Path("data/metadata/test_config.json")
TEST_SET_PATH = Path("data/processed/test_set.csv")
TEST_INDICES_PATH = Path("data/processed/test_set_indices.csv")
TEST_METADATA_PATH = Path("data/metadata/test_set_metadata.json")

def load_data():
    """Load the raw pool CSV. Fails loudly if missing."""
    if not RAW_POOL_PATH.exists():
        raise RuntimeError(
            f"CRITICAL: Input file {RAW_POOL_PATH} does not exist. "
            "Task T024 (data ingestion) must complete successfully before T020 can run. "
            "Do not generate synthetic data."
        )
    logger.info(f"Loading raw pool from {RAW_POOL_PATH}")
    df = pd.read_csv(RAW_POOL_PATH)
    logger.info(f"Loaded {len(df)} rows from raw pool.")
    return df

def load_test_config():
    """Load test configuration (size) from metadata. Fails loudly if missing."""
    if not TEST_CONFIG_PATH.exists():
        raise RuntimeError(
            f"CRITICAL: Test configuration file {TEST_CONFIG_PATH} does not exist. "
            "Please ensure T005 or the planning phase has generated the test size configuration."
        )
    with open(TEST_CONFIG_PATH, 'r') as f:
        config = json.load(f)
    
    if 'test_size' not in config:
        raise RuntimeError(f"CRITICAL: 'test_size' key missing in {TEST_CONFIG_PATH}")
    
    return config['test_size']

def create_test_set(df, test_size, seed=42):
    """
    Create a stratified test set based on formation_energy bins.
    
    Algorithm:
    1. Use pd.qcut to create quantile bins on 'formation_energy'.
    2. Sample 'test_size' rows stratified by these bins.
    """
    logger.info(f"Creating stratified test set of size {test_size} with seed {seed}")
    
    # Ensure formation_energy exists
    if 'formation_energy' not in df.columns:
        raise ValueError("Column 'formation_energy' not found in raw pool. Cannot stratify.")
    
    # Drop rows with NaN in formation_energy for binning purposes, but we need to handle them carefully
    # For stratification, we only consider rows with valid formation_energy
    valid_mask = df['formation_energy'].notna()
    valid_df = df[valid_mask].copy()
    
    if len(valid_df) == 0:
        raise ValueError("No rows with valid 'formation_energy' found for stratification.")
    
    # Create bins using qcut. We'll use 10 quantile bins for good stratification
    n_bins = 10
    try:
        bins = pd.qcut(valid_df['formation_energy'], q=n_bins, duplicates='drop')
    except ValueError as e:
        # Fallback to fewer bins if not enough unique values
        logger.warning(f"qcut failed with {n_bins} bins: {e}. Trying fewer bins.")
        bins = pd.qcut(valid_df['formation_energy'], q=min(n_bins, len(valid_df)), duplicates='drop')
    
    valid_df['stratum'] = bins
    
    # Calculate how many to sample per stratum
    stratum_counts = valid_df['stratum'].value_counts()
    total_valid = len(valid_df)
    
    # Proportional allocation
    sample_counts = (stratum_counts / total_valid * test_size).round().astype(int)
    
    # Ensure we don't exceed available rows in any stratum
    sample_counts = sample_counts.clip(upper=stratum_counts)
    
    # Adjust to match exact test_size if rounding caused mismatch
    current_sum = sample_counts.sum()
    if current_sum != test_size:
        diff = test_size - current_sum
        if diff > 0:
            # Add to largest strata
            largest_strata = sample_counts.sort_values(ascending=False).index[:diff]
            for idx in largest_strata:
                if sample_counts[idx] < stratum_counts[idx]:
                    sample_counts[idx] += 1
        else:
            # Remove from smallest non-zero strata
            smallest_strata = sample_counts.sort_values(ascending=True).index
            for idx in smallest_strata:
                if sample_counts[idx] > 0:
                    sample_counts[idx] -= 1
                    diff += 1
                    if diff == 0:
                        break
    
    # Sample from each stratum
    test_indices = []
    for stratum, count in sample_counts.items():
        stratum_df = valid_df[valid_df['stratum'] == stratum]
        sampled = stratum_df.sample(n=count, random_state=seed)
        test_indices.extend(sampled.index.tolist())
    
    test_df = df.loc[test_indices].copy()
    
    logger.info(f"Test set created with {len(test_df)} rows.")
    return test_df, test_indices

def save_test_set(test_df):
    """Save the test set DataFrame to CSV."""
    TEST_SET_PATH.parent.mkdir(parents=True, exist_ok=True)
    test_df.to_csv(TEST_SET_PATH, index=False)
    logger.info(f"Saved test set to {TEST_SET_PATH}")
    return TEST_SET_PATH

def save_indices(indices):
    """Save the list of indices to a CSV file."""
    TEST_INDICES_PATH.parent.mkdir(parents=True, exist_ok=True)
    indices_df = pd.DataFrame({'index': indices})
    indices_df.to_csv(TEST_INDICES_PATH, index=False)
    logger.info(f"Saved test indices to {TEST_INDICES_PATH}")
    return TEST_INDICES_PATH

def save_metadata(test_df, indices):
    """Generate and save metadata about the test set."""
    checksum = compute_sha256(TEST_SET_PATH)
    metadata = {
        "row_count": len(test_df),
        "seed": 42,
        "checksum": checksum,
        "creation_timestamp": pd.Timestamp.now().isoformat(),
        "source_file": str(RAW_POOL_PATH),
        "stratification_column": "formation_energy"
    }
    
    TEST_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TEST_METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved test set metadata to {TEST_METADATA_PATH}")
    return metadata

def main():
    """Main entry point for the test split task."""
    parser = argparse.ArgumentParser(description="Split raw pool into fixed test set.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()
    
    try:
        # 1. Load raw pool (fails if missing)
        df = load_data()
        
        # 2. Load test config (fails if missing)
        test_size = load_test_config()
        
        # 3. Create test set
        test_df, indices = create_test_set(df, test_size, seed=args.seed)
        
        # 4. Save outputs
        save_test_set(test_df)
        save_indices(indices)
        save_metadata(test_df, indices)
        
        logger.info("Task T020 completed successfully.")
        
    except RuntimeError as e:
        logger.error(f"Runtime Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
