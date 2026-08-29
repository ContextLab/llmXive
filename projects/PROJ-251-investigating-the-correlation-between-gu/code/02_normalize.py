import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import numpy as np

from utils.config import get_lod_handling_methods, get_min_sample_size, get_random_seed
from utils.logging_config import get_logger, log_exclusion_count, log_sample_size
from utils.validators import validate_dataframe_not_empty

logger = get_logger(__name__)

def load_merged_data(input_path: Path) -> pd.DataFrame:
    """
    Load the merged dataset from T011d.
    """
    logger.info(f"Loading merged data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    return df

def normalize_to_relative_abundance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize OTU table to relative abundance.
    
    For each subject (row), sum the abundances of all taxon columns,
    then divide each taxon value by that sum.
    
    Excludes non-taxon columns (subject_id, titers, etc.) from normalization.
    """
    logger.info("Normalizing to relative abundance")
    
    # Identify taxon columns (exclude known metadata columns)
    metadata_cols = ['subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity']
    # Dynamically detect taxon columns: all columns not in metadata and numeric
    taxon_cols = [col for col in df.columns 
                 if col not in metadata_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    if not taxon_cols:
        raise ValueError("No taxon columns found for normalization")
    
    logger.info(f"Found {len(taxon_cols)} taxon columns to normalize")
    
    # Calculate row sums for taxon columns
    row_sums = df[taxon_cols].sum(axis=1)
    
    # Handle zero-sum rows (subjects with no taxa)
    zero_sum_mask = row_sums == 0
    if zero_sum_mask.any():
        zero_count = zero_sum_mask.sum()
        logger.warning(f"Found {zero_count} subjects with zero total abundance")
        # Replace zero sums with 1 to avoid division by zero, then set resulting values to 0
        row_sums = row_sums.replace(0, 1)
    
    # Normalize
    normalized_df = df.copy()
    for col in taxon_cols:
        normalized_df[col] = df[col] / row_sums
    
    # Verify normalization (sum should be ~1.0 for each row)
    check_sums = normalized_df[taxon_cols].sum(axis=1)
    non_unit_sums = check_sums[(check_sums < 0.99) | (check_sums > 1.01)]
    if len(non_unit_sums) > 0:
        logger.warning(f"{len(non_unit_sums)} rows have normalized sums outside [0.99, 1.01]")
    
    logger.info("Normalization complete")
    return normalized_df

def run_normalization_pipeline(
    input_path: Path,
    output_path: Path,
    min_sample_size: Optional[int] = None
) -> Path:
    """
    Run the full normalization pipeline.
    
    Args:
        input_path: Path to merged data (data/processed/data_merged.csv)
        output_path: Path to write normalized data (data/processed/data_norm.csv)
        min_sample_size: Minimum required sample size (from config)
    
    Returns:
        Path to the output file
    """
    logger.info("Starting normalization pipeline")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = load_merged_data(input_path)
    
    # Validate input is not empty
    validate_dataframe_not_empty(df, "input merged data")
    
    # Check sample size
    if min_sample_size is None:
        min_sample_size = get_min_sample_size()
    
    if len(df) < min_sample_size:
        logger.error(f"Sample size {len(df)} is below minimum {min_sample_size}")
        raise ValueError(f"Insufficient sample size: {len(df)} < {min_sample_size}")
    
    log_sample_size(len(df))
    
    # Normalize
    normalized_df = normalize_to_relative_abundance(df)
    
    # Validate output is not empty
    validate_dataframe_not_empty(normalized_df, "normalized data")
    
    # Write output
    normalized_df.to_csv(output_path, index=False)
    logger.info(f"Wrote normalized data to {output_path}")
    
    # Log completion
    log_sample_size(len(normalized_df))
    
    return output_path

def main():
    """Main entry point for normalization script."""
    # Set up paths
    base_dir = Path(__file__).parent.parent
    input_path = base_dir / "data" / "processed" / "data_merged.csv"
    output_path = base_dir / "data" / "processed" / "data_norm.csv"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(base_dir / "data" / "results" / "normalization.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    try:
        result_path = run_normalization_pipeline(input_path, output_path)
        logger.info(f"Normalization completed successfully. Output: {result_path}")
        return 0
    except Exception as e:
        logger.error(f"Normalization failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
