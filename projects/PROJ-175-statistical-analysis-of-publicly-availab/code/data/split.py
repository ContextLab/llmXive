"""
Task T019: Train/Test Split
Downsamples to N_unified (from T008) with fixed seed; writes splits and updates data/split_config.json.
Dependencies: T008 (Power Analysis), T018 (Imputation & Bias Check)
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure project root is in path
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from code.utils.memory_monitor import check_memory_limit

# Constants
DATA_DIR = ROOT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
FINAL_DIR = DATA_DIR / "final"

# Input files from prerequisites
POWER_ANALYSIS_FILE = DATA_DIR / "power_analysis.json"
IMPUTED_FEATURES_FILE = PROCESSED_DIR / "final_features.parquet"
SPLIT_CONFIG_FILE = DATA_DIR / "split_config.json"

# Output files
TRAIN_SET_FILE = PROCESSED_DIR / "train_set.parquet"
TEST_SET_FILE = PROCESSED_DIR / "test_set.parquet"

def load_subset_size():
    """Load N_unified from power analysis result."""
    if not POWER_ANALYSIS_FILE.exists():
        raise FileNotFoundError(f"Power analysis file not found: {POWER_ANALYSIS_FILE}. Run T008 first.")
    
    with open(POWER_ANALYSIS_FILE, 'r') as f:
        config = json.load(f)
    
    n_unified = config.get('N_unified')
    if n_unified is None or n_unified == 'deferred':
        # Fallback to a conservative default if power analysis failed or was deferred
        n_unified = 1000
        print(f"Warning: N_unified is 'deferred' or missing. Using fallback value: {n_unified}")
    
    return int(n_unified)

def load_processed_data():
    """Load the imputed features dataset from T018."""
    if not IMPUTED_FEATURES_FILE.exists():
        raise FileNotFoundError(f"Imputed features file not found: {IMPUTED_FEATURES_FILE}. Run T018 first.")
    
    df = pd.read_parquet(IMPUTED_FEATURES_FILE)
    
    if df.empty:
        raise ValueError("Input dataset is empty. Cannot proceed with splitting.")
    
    return df

def create_train_test_split():
    """
    Downsample to N_unified, split into train/test, and save outputs.
    """
    # Check memory limit
    check_memory_limit(limit_mb=7168)
    
    # Load configuration
    n_unified = load_subset_size()
    seed = 42  # Fixed seed as per project requirements
    
    # Load data
    df = load_processed_data()
    
    print(f"Loaded {len(df)} rows. Target sample size: {n_unified}")
    
    # Downsample if necessary
    if len(df) > n_unified:
        # Use a fixed seed for reproducibility
        df_sample = df.sample(n=n_unified, random_state=seed).reset_index(drop=True)
        print(f"Downsampled from {len(df)} to {n_unified} rows.")
    else:
        df_sample = df.copy()
        print(f"Dataset size ({len(df)}) is within target ({n_unified}). No downsampling needed.")
    
    # Calculate split sizes (80/20)
    train_size = int(len(df_sample) * 0.8)
    test_size = len(df_sample) - train_size
    
    print(f"Splitting into train ({train_size}) and test ({test_size}) sets.")
    
    # Perform split with fixed seed
    train_df, test_df = train_test_split(
        df_sample, 
        train_size=train_size, 
        random_state=seed
    )
    
    # Ensure directories exist
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save splits
    train_df.to_parquet(TRAIN_SET_FILE, index=False)
    test_df.to_parquet(TEST_SET_FILE, index=False)
    
    print(f"Saved train set to {TRAIN_SET_FILE}")
    print(f"Saved test set to {TEST_SET_FILE}")
    
    # Update split config
    split_config = {
        "N_unified": n_unified,
        "train_size": train_size,
        "test_size": test_size,
        "seed": seed,
        "original_size": len(df),
        "downsampled": len(df) > n_unified,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open(SPLIT_CONFIG_FILE, 'w') as f:
        json.dump(split_config, f, indent=2)
    
    print(f"Updated split config at {SPLIT_CONFIG_FILE}")
    
    return split_config

def train_test_split(df, train_size, random_state):
    """
    Simple train/test split implementation to avoid sklearn dependency issues if any.
    """
    np.random.seed(random_state)
    indices = np.random.permutation(len(df))
    train_idx = indices[:train_size]
    test_idx = indices[train_size:]
    
    return df.iloc[train_idx].reset_index(drop=True), df.iloc[test_idx].reset_index(drop=True)

def main():
    """Main entry point for T019."""
    try:
        print("Starting T019: Train/Test Split")
        config = create_train_test_split()
        print("T019 completed successfully.")
        return 0
    except Exception as e:
        print(f"T019 failed: {e}")
        # Log error to a specific file for pipeline tracking
        error_log = DATA_DIR / "pipeline_errors.json"
        error_data = {
            "task": "T019",
            "error": str(e),
            "timestamp": pd.Timestamp.now().isoformat()
        }
        with open(error_log, 'w') as f:
            json.dump(error_data, f, indent=2)
        return 1

if __name__ == "__main__":
    sys.exit(main())
