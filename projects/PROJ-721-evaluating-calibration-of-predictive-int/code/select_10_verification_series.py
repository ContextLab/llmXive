"""
Select a small verification sub-sample (10 series) from the 1000-series sample.

This task implements T013c: Verification Sub-sample.
It loads the indices selected in T013b (sample_indices_1000.csv) and selects
a deterministic subset of 10 series for manual verification of coverage logic.

Dependencies:
    - data/processed/sample_indices_1000.csv (produced by T013b)
    - config.yaml (for random seed)

Output:
    - data/processed/sample_indices_10.csv
"""

import json
import logging
import os
import sys
from typing import List, Dict, Any

import pandas as pd
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def load_1000_sample_indices(sample_path: str = "data/processed/sample_indices_1000.csv") -> pd.DataFrame:
    """
    Load the 1000-series sample indices.
    
    Args:
        sample_path: Path to the CSV file containing the 1000 series indices.
        
    Returns:
        DataFrame with the sample indices.
        
    Raises:
        FileNotFoundError: If the sample file does not exist.
        ValueError: If the file does not contain expected columns.
    """
    if not os.path.exists(sample_path):
        raise FileNotFoundError(
            f"1000-series sample file not found: {sample_path}. "
            f"Ensure T013b has been completed successfully."
        )
    
    df = pd.read_csv(sample_path)
    
    # Verify expected columns
    expected_cols = ['series_id']
    if not all(col in df.columns for col in expected_cols):
        raise ValueError(
            f"Sample file must contain columns: {expected_cols}. "
            f"Found: {list(df.columns)}"
        )
    
    logger.info(f"Loaded {len(df)} series from {sample_path}")
    return df


def select_verification_subset(
    df: pd.DataFrame, 
    n_series: int = 10, 
    seed: int = 42
) -> pd.DataFrame:
    """
    Select a deterministic subset of series for verification.
    
    Args:
        df: DataFrame containing the 1000-series sample.
        n_series: Number of series to select (default: 10).
        seed: Random seed for reproducibility.
        
    Returns:
        DataFrame containing the selected verification subset.
        
    Raises:
        ValueError: If the input DataFrame has fewer series than requested.
    """
    if len(df) < n_series:
        raise ValueError(
            f"Cannot select {n_series} series from a sample of {len(df)}. "
            f"The 1000-series sample is too small."
        )
    
    # Use deterministic selection based on seed
    # This ensures the same 10 series are selected every time for verification
    verification_df = df.sample(n=n_series, random_state=seed).reset_index(drop=True)
    
    logger.info(f"Selected {n_series} verification series (seed={seed})")
    return verification_df


def save_verification_indices(df: pd.DataFrame, output_path: str = "data/processed/sample_indices_10.csv") -> None:
    """
    Save the verification subset to a CSV file.
    
    Args:
        df: DataFrame containing the selected verification series.
        output_path: Path where the output CSV will be saved.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved verification indices to {output_path}")
    logger.info(f"Series IDs: {list(df['series_id'])}")


def main():
    """Main entry point for T013c."""
    try:
        # Load configuration for seed
        config = load_config("config.yaml")
        seed = config.get("seed", 42)
        logger.info(f"Using random seed: {seed}")
        
        # Load the 1000-series sample
        sample_1000_df = load_1000_sample_indices()
        
        # Select verification subset
        verification_df = select_verification_subset(sample_1000_df, n_series=10, seed=seed)
        
        # Save the result
        save_verification_indices(verification_df)
        
        logger.info("T013c completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())