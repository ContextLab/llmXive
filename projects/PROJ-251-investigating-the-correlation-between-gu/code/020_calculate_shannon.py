"""
T020c: Shannon Diversity Calculation
Calculates the Shannon diversity index from microbiome taxon columns
and appends the result to the cleared dataset.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_processed_path, get_random_seed
from utils.logging_config import get_logger, log_sample_size

# Configure logger
logger = get_logger(__name__)

def load_cleared_data(input_path: Path) -> pd.DataFrame:
    """Load the cleared dataset from the previous step."""
    logger.info(f"Loading cleared data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded dataset with shape: {df.shape}")
    return df

def identify_taxa_columns(df: pd.DataFrame) -> list:
    """
    Identify columns representing taxa abundances.
    Assumes columns are numeric and NOT subject_id or titer columns.
    """
    exclude_cols = {'subject_id', 'titer_baseline', 'titer_post'}
    taxa_cols = []
    
    for col in df.columns:
        if col in exclude_cols:
            continue
        # Check if column is numeric
        if pd.api.types.is_numeric_dtype(df[col]):
            taxa_cols.append(col)
    
    if not taxa_cols:
        raise ValueError("No numeric taxa columns found in the dataset.")
    
    logger.info(f"Identified {len(taxa_cols)} taxa columns: {taxa_cols[:5]}...")
    return taxa_cols

def calculate_shannon_diversity(df: pd.DataFrame, taxa_cols: list) -> pd.Series:
    """
    Calculate Shannon diversity index for each row.
    Formula: H = -sum(p_i * ln(p_i)) for p_i > 0
    where p_i is the relative abundance of taxon i.
    """
    # Extract taxa data
    taxa_data = df[taxa_cols].values
    
    # Ensure non-negative (abundances should be >= 0)
    if np.any(taxa_data < 0):
        logger.warning("Negative values found in taxa data. Taking absolute value.")
        taxa_data = np.abs(taxa_data)
    
    # Calculate row sums (total abundance per sample)
    row_sums = taxa_data.sum(axis=1)
    
    # Avoid division by zero
    row_sums[row_sums == 0] = 1.0
    
    # Calculate relative abundances
    p = taxa_data / row_sums[:, np.newaxis]
    
    # Calculate Shannon index: -sum(p * ln(p)) for p > 0
    # Use np.where to handle p=0 cases (0 * ln(0) -> 0)
    log_p = np.log(p)
    log_p = np.where(p > 0, log_p, 0.0)
    shannon = -np.sum(p * log_p, axis=1)
    
    return pd.Series(shannon, index=df.index, name='shannon_diversity')

def write_updated_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Write the updated dataset with Shannon diversity to CSV."""
    logger.info(f"Writing updated dataset to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(df)} rows to {output_path}")

def run_shannon_pipeline(input_path: Path, output_path: Path) -> None:
    """
    Run the full Shannon diversity calculation pipeline.
    """
    logger.info("Starting Shannon diversity calculation pipeline")
    
    # Load data
    df = load_cleared_data(input_path)
    
    # Identify taxa columns
    taxa_cols = identify_taxa_columns(df)
    
    # Calculate Shannon diversity
    shannon_series = calculate_shannon_diversity(df, taxa_cols)
    
    # Add to dataframe
    df['shannon_diversity'] = shannon_series
    
    # Log sample size
    log_sample_size(len(df), "shannon_diversity")
    
    # Write output
    write_updated_dataset(df, output_path)
    
    logger.info("Shannon diversity calculation pipeline completed successfully")

def main():
    """Main entry point for the script."""
    # Define paths
    input_path = get_processed_path() / "cleared.csv"
    output_path = get_processed_path() / "cleared_shannon.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        run_shannon_pipeline(input_path, output_path)
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during pipeline execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
