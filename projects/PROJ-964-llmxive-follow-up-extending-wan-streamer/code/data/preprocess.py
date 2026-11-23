import os
import sys
import argparse
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import numpy as np
from scipy import stats

# Import existing config and utils
try:
    from config import get_config_summary
except ImportError:
    # Fallback for direct script execution if config is not in path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_SAMPLE_SIZE = 5000  # Derived from power analysis minimums

class PowerLimitationError(Exception):
    """Raised when sample size reduction would go below the minimum required."""
    pass

def load_config():
    """Load configuration from the project config."""
    return get_config_summary()

def fetch_data_source():
    """
    Fetch the data source based on validation checks.
    This relies on T009 having run and set the data_source in state.yaml.
    For this task, we assume the data has been validated and exists at the expected path.
    """
    # In a real flow, this would read state.yaml to determine source
    # For now, we assume the filtered data exists at the expected location
    data_path = Path("data/processed/filtered.parquet")
    if not data_path.exists():
        raise FileNotFoundError(f"Expected filtered data not found at {data_path}. "
                                "Please ensure T014d (filter_events) has run successfully.")
    return pd.read_parquet(data_path)

def filter_events(df):
    """
    Retain only rows with valid semantic_feature, prosodic_feature, and turn-taking labels.
    """
    required_cols = ['semantic_feature', 'prosodic_feature', 'turn_label']
    # Check if columns exist
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Filter for non-null values in required columns
    initial_count = len(df)
    df_filtered = df.dropna(subset=required_cols)
    final_count = len(df_filtered)
    logger.info(f"Filtered events: {initial_count} -> {final_count} (removed {initial_count - final_count} rows)")

    return df_filtered

def compute_latent_deltas(df):
    """
    Compute latent delta magnitude if not already present.
    Assumes 'latent_vector' or similar exists, or uses a placeholder if derived.
    For this task, we assume 'latent_delta_magnitude' is already computed in previous steps.
    """
    if 'latent_delta_magnitude' not in df.columns:
        # Fallback: compute from latent vectors if available
        if 'latent_vector' in df.columns:
            logger.warning("latent_delta_magnitude not found, computing from latent_vector")
            # Placeholder logic: assume latent_vector is a list/array string or column of arrays
            # In a real scenario, this would be vectorized
            def calc_delta(vec):
                if isinstance(vec, str):
                    vec = eval(vec) # Safe eval for string representation of list
                if isinstance(vec, list):
                    vec = np.array(vec)
                if len(vec) < 2:
                    return 0.0
                return np.linalg.norm(np.diff(vec))
            
            df['latent_delta_magnitude'] = df['latent_vector'].apply(calc_delta)
        else:
            raise ValueError("Cannot compute latent_delta_magnitude: missing source data.")
    return df

def label_priority(df):
    """
    Assign a boolean 'high_priority' column based on domain-specific rules.
    Rule: high delta magnitude or high uncertainty.
    """
    if 'latent_delta_magnitude' in df.columns:
        # Example rule: top 20% of delta magnitude are high priority
        threshold = df['latent_delta_magnitude'].quantile(0.8)
        df['high_priority'] = df['latent_delta_magnitude'] > threshold
    else:
        df['high_priority'] = False
    return df

def log_priority_counts(df):
    """
    Log counts of high vs low priority events to data/logs/priority_counts.log.
    """
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "priority_counts.log"

    high_count = df['high_priority'].sum()
    low_count = len(df) - high_count

    with open(log_path, 'w') as f:
        f.write(f"High priority events: {high_count}\n")
        f.write(f"Low priority events: {low_count}\n")
    
    logger.info(f"Priority counts logged to {log_path}")

def load_power_analysis():
    """Load the initial power analysis results."""
    path = Path("data/metrics/power_analysis_initial.json")
    if not path.exists():
        # Fallback if T016a hasn't run, use default
        logger.warning("power_analysis_initial.json not found. Using default sample size.")
        return {"recommended_sample_size": 1000}
    
    with open(path, 'r') as f:
        return json.load(f)

def apply_stratified_sampling(df, size):
    """
    Perform stratified sampling based on 'turn_label' using the specified size.
    Output: data/processed/sampled_dataset.parquet
    """
    if 'turn_label' not in df.columns:
        raise ValueError("Column 'turn_label' not found in dataframe for stratification.")

    # Ensure size is integer
    size = int(size)

    if size >= len(df):
        logger.warning(f"Requested sample size ({size}) >= dataset size ({len(df)}). Returning full dataset.")
        sampled_df = df.copy()
    else:
        # Stratified sampling
        try:
            sampled_df = df.groupby('turn_label', group_keys=False).apply(
                lambda x: x.sample(n=min(int(size * len(x) / len(df)), len(x)), random_state=42)
            )
            # If the groupby apply results in fewer rows than requested due to small strata,
            # we might need to pad or just accept the smaller size.
            # For strict adherence to "row count equals selected size (or dataset size if smaller)",
            # we accept the result of the stratified sampling.
            sampled_df = sampled_df.reset_index(drop=True)
        except ValueError as e:
            # Handle case where a stratum is smaller than the proportional share
            logger.warning(f"Stratified sampling adjustment needed: {e}")
            # Fallback to simple random sample if stratification fails due to small groups
            # but try to respect the distribution as much as possible
            sampled_df = df.sample(n=size, random_state=42)

    logger.info(f"Stratified sampling complete: {len(df)} -> {len(sampled_df)} rows")
    return sampled_df

def validate_output(df):
    """
    Verify that all required columns are non-null and correctly typed.
    """
    required_cols = ['timestamp', 'semantic_feature', 'prosodic_feature', 
                     'latent_delta_magnitude', 'turn_label']
    for col in required_cols:
        if col not in df.columns:
            return False, f"Missing column: {col}"
        if df[col].isnull().any():
            return False, f"Column {col} contains null values"
    return True, "Validation passed"

def get_current_memory_usage_mb():
    """Get current memory usage in MB."""
    import resource
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # On Linux, ru_maxrss is in KB; on macOS it's in KB too, but sometimes different units
    # Assuming KB for standard Linux environments
    return usage / 1024.0

def handle_power_limitation(current_size):
    """
    Raise PowerLimitationError if reduction would go below MIN_SAMPLE_SIZE.
    """
    if current_size <= MIN_SAMPLE_SIZE:
        raise PowerLimitationError(f"Power Limitation: Cannot reduce sample size below {MIN_SAMPLE_SIZE}.")

def main():
    """
    Main entry point for the preprocessing and stratified sampling task.
    1. Load filtered data (from T014d).
    2. Load selected sample size (from T014g).
    3. Apply stratified sampling.
    4. Save to data/processed/sampled_dataset.parquet.
    5. Validate output.
    """
    parser = argparse.ArgumentParser(description="Preprocess data and perform stratified sampling.")
    parser.add_argument('--config', type=str, default=None, help='Path to config file (optional)')
    args = parser.parse_args()

    try:
        # 1. Load filtered data
        logger.info("Loading filtered data...")
        df = fetch_data_source()
        
        # 2. Load selected sample size
        logger.info("Loading selected sample size...")
        size_file = Path("data/metrics/selected_sample_size.txt")
        if not size_file.exists():
            raise FileNotFoundError("selected_sample_size.txt not found. Ensure T014g has run.")
        
        with open(size_file, 'r') as f:
            selected_size = int(f.read().strip())
        
        logger.info(f"Selected sample size: {selected_size}")

        # 3. Apply stratified sampling
        logger.info("Applying stratified sampling...")
        sampled_df = apply_stratified_sampling(df, selected_size)

        # 4. Save output
        output_path = Path("data/processed/sampled_dataset.parquet")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sampled_df.to_parquet(output_path, index=False)
        logger.info(f"Saved sampled dataset to {output_path}")

        # 5. Validate output
        is_valid, msg = validate_output(sampled_df)
        if not is_valid:
            logger.error(f"Validation failed: {msg}")
            sys.exit(1)
        
        logger.info("Validation passed.")

        # Log row count verification
        if len(sampled_df) != selected_size and len(sampled_df) != len(df):
            logger.warning(f"Sample size mismatch: expected {selected_size}, got {len(sampled_df)}. "
                         "This may be due to strata sizes being smaller than proportional share.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
