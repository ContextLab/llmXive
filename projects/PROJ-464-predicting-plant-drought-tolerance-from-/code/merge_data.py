"""
Merge RSA metrics with physiological trait data.

Implements strict listwise deletion for missing species and enforces
the minimum sample size constraint (N >= 55) as per project specifications.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd

# Import project config for paths
from config import ensure_directories, get_config_summary

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_rsa_metrics(input_path: Path) -> pd.DataFrame:
    """Load RSA metrics from the derived CSV."""
    if not input_path.exists():
        raise FileNotFoundError(f"RSA metrics file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded RSA metrics: {len(df)} rows, columns: {list(df.columns)}")
    return df

def load_physiological_data(input_path: Path) -> pd.DataFrame:
    """Load physiological trait data from the derived CSV."""
    if not input_path.exists():
        raise FileNotFoundError(f"Physiological data file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded physiological data: {len(df)} rows, columns: {list(df.columns)}")
    return df

def merge_datasets(
    rsa_df: pd.DataFrame, 
    physio_df: pd.DataFrame, 
    key_col: str = "species_id"
) -> pd.DataFrame:
    """
    Merge RSA and physiological data using inner join (listwise deletion).
    
    This implements strict listwise deletion: any species missing from either
    dataset is removed from the final merged dataset.
    
    Args:
        rsa_df: DataFrame containing RSA metrics
        physio_df: DataFrame containing physiological traits
        key_col: Column name to join on (default: species_id)
        
    Returns:
        Merged DataFrame with only species present in both datasets
    """
    # Perform inner join to enforce listwise deletion
    merged = pd.merge(
        rsa_df, 
        physio_df, 
        on=key_col, 
        how="inner",
        suffixes=('_rsa', '_physio')
    )
    
    logger.info(f"Merged dataset size: {len(merged)} rows")
    logger.info(f"Columns in merged dataset: {list(merged.columns)}")
    
    return merged

def validate_sample_size(merged_df: pd.DataFrame, min_size: int = 55) -> bool:
    """
    Validate that the merged dataset meets the minimum sample size requirement.
    
    Args:
        merged_df: The merged DataFrame
        min_size: Minimum required sample size (default: 55)
        
    Returns:
        True if sample size is sufficient, False otherwise
        
    Raises:
        RuntimeError: If sample size is below minimum
    """
    n = len(merged_df)
    if n < min_size:
        error_msg = f"Insufficient species after merge (N = {n} < {min_size}). Pipeline halted."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info(f"Sample size validation passed: N = {n} >= {min_size}")
    return True

def main():
    """Main entry point for data merging."""
    try:
        # Get configuration and ensure directories exist
        config = get_config_summary()
        ensure_directories()
        
        # Define paths
        rsa_metrics_path = Path("data/derived/rsametrics.csv")
        physio_data_path = Path("data/derived/physio_traits.csv")
        output_path = Path("data/derived/merged_dataset.csv")
        
        logger.info(f"Starting data merge process...")
        logger.info(f"RSA metrics source: {rsa_metrics_path}")
        logger.info(f"Physiological data source: {physio_data_path}")
        logger.info(f"Output destination: {output_path}")
        
        # Load datasets
        rsa_df = load_rsa_metrics(rsa_metrics_path)
        physio_df = load_physiological_data(physio_data_path)
        
        # Merge datasets (listwise deletion)
        merged_df = merge_datasets(rsa_df, physio_df)
        
        # Validate sample size (strict constraint)
        validate_sample_size(merged_df, min_size=55)
        
        # Save merged dataset
        output_path.parent.mkdir(parents=True, exist_ok=True)
        merged_df.to_csv(output_path, index=False)
        
        logger.info(f"Successfully saved merged dataset to {output_path}")
        logger.info(f"Final dataset shape: {merged_df.shape}")
        logger.info(f"Columns: {list(merged_df.columns)}")
        
        # Print summary
        print(f"\nMerge Summary:")
        print(f"  Input RSA rows: {len(rsa_df)}")
        print(f"  Input Physio rows: {len(physio_df)}")
        print(f"  Merged rows: {len(merged_df)}")
        print(f"  Listwise deletion: {len(rsa_df) + len(physio_df) - 2*len(merged_df)} species removed")
        print(f"  Sample size check: PASSED (N={len(merged_df)} >= 55)")
        
    except FileNotFoundError as e:
        logger.critical(f"Data file missing: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.critical(f"Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during merge: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()