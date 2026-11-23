import os
import sys
import logging
from pathlib import Path
from typing import List, Optional
import pandas as pd
import numpy as np

# Import logging configuration from existing utils
from utils.logging_config import get_logger

def load_merged_data(input_path: str) -> pd.DataFrame:
    """
    Load the merged dataset from the specified CSV file.
    
    Args:
        input_path: Path to the input CSV file.
        
    Returns:
        pandas DataFrame containing the merged data.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or unreadable.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError(f"Input file is empty: {input_path}")
        
    return df

def identify_taxa_columns(df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> List[str]:
    """
    Identify microbiome taxon columns in the DataFrame.
    
    Excludes specified columns (default: subject_id and titer columns).
    Assumes taxon columns are numeric.
    
    Args:
        df: Input DataFrame.
        exclude_cols: List of column names to exclude.
        
    Returns:
        List of taxon column names.
    """
    if exclude_cols is None:
        exclude_cols = ['subject_id', 'titer_baseline', 'titer_post']
    
    # Get all numeric columns that are not in the exclude list
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    taxa_cols = [col for col in numeric_cols if col not in exclude_cols]
    
    return taxa_cols

def normalize_to_relative_abundance(df: pd.DataFrame, taxa_cols: List[str]) -> pd.DataFrame:
    """
    Normalize microbiome taxon abundances to relative abundance (sum=1 per row).
    
    Args:
        df: Input DataFrame.
        taxa_cols: List of taxon column names to normalize.
        
    Returns:
        DataFrame with normalized taxon abundances.
        
    Raises:
        ValueError: If row sums are zero for any subject.
    """
    # Create a copy to avoid modifying the original
    df_normalized = df.copy()
    
    # Calculate row sums for taxon columns
    row_sums = df_normalized[taxa_cols].sum(axis=1)
    
    # Check for zero sums (which would cause division by zero)
    if (row_sums == 0).any():
        zero_sum_mask = row_sums == 0
        raise ValueError(
            f"Found {zero_sum_mask.sum()} subjects with zero total abundance. "
            "Cannot normalize to relative abundance."
        )
    
    # Normalize each taxon column by the row sum
    for col in taxa_cols:
        df_normalized[col] = df_normalized[col] / row_sums
    
    # Verification: Assert that the sum of taxon columns for each row is 1.0 (within tolerance)
    verification_sums = df_normalized[taxa_cols].sum(axis=1)
    if not np.allclose(verification_sums, 1.0, rtol=1e-5):
        raise AssertionError(
            f"Normalization verification failed. "
            f"Row sums are not 1.0. Min: {verification_sums.min()}, Max: {verification_sums.max()}"
        )
    
    return df_normalized

def write_updated_dataset(df: pd.DataFrame, output_path: str) -> None:
    """
    Write the updated dataset to a CSV file.
    
    Args:
        df: DataFrame to write.
        output_path: Path to the output CSV file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logging.info(f"Normalized dataset written to: {output_path}")

def run_normalization_pipeline(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Run the full normalization pipeline: load, identify taxa, normalize, and save.
    
    Args:
        input_path: Path to the input CSV file.
        output_path: Path to the output CSV file.
        
    Returns:
        The normalized DataFrame.
    """
    logger = get_logger(__name__)
    logger.info(f"Starting normalization pipeline for: {input_path}")
    
    # Load data
    df = load_merged_data(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Identify taxon columns
    taxa_cols = identify_taxa_columns(df)
    logger.info(f"Identified {len(taxa_cols)} taxon columns for normalization")
    
    if len(taxa_cols) == 0:
        raise ValueError("No taxon columns found in the dataset.")
    
    # Normalize
    df_normalized = normalize_to_relative_abundance(df, taxa_cols)
    logger.info("Normalization completed successfully")
    
    # Write output
    write_updated_dataset(df_normalized, output_path)
    
    return df_normalized

def main():
    """Main entry point for the normalization script."""
    # Define paths relative to project root
    input_file = "data/processed/cleared.csv"
    output_file = "data/processed/cleared_norm.csv"
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        run_normalization_pipeline(input_file, output_file)
        logging.info("Normalization pipeline completed successfully.")
    except Exception as e:
        logging.error(f"Normalization pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
