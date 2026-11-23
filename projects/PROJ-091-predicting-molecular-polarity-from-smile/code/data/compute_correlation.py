"""
T014b: Compute Pearson correlation between every descriptor and the target dipole moment.

Input: data/processed/descriptors.parquet (produced by T018)
Output: data/processed/correlation_matrix.csv
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

def compute_correlation_matrix(input_path: str, output_path: str) -> None:
    """
    Compute Pearson correlation between every descriptor and the target dipole moment.
    
    Args:
        input_path: Path to the input parquet file containing descriptors
        output_path: Path to write the correlation matrix CSV
    """
    logger.info(f"Loading descriptors from {input_path}")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load the parquet file
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
    
    # Identify the target column (dipole moment)
    target_col = 'target'
    if target_col not in df.columns:
        logger.error(f"Target column '{target_col}' not found in dataframe. Available columns: {list(df.columns)}")
        raise ValueError(f"Target column '{target_col}' not found in dataframe")
    
    # Separate numeric descriptor columns (excluding 'smiles' and 'target')
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    descriptor_cols = [col for col in numeric_cols if col != target_col]
    
    logger.info(f"Computing correlations for {len(descriptor_cols)} descriptors against target")
    
    if len(descriptor_cols) == 0:
        logger.error("No numeric descriptor columns found")
        raise ValueError("No numeric descriptor columns found")
    
    # Compute Pearson correlation between each descriptor and the target
    correlations = {}
    for col in descriptor_cols:
        # Compute Pearson correlation, handling NaNs
        corr = df[col].corr(df[target_col], method='pearson')
        correlations[col] = corr
    
    # Create a DataFrame for the correlation matrix
    # Format: one row per descriptor, columns for 'descriptor', 'correlation', 'abs_correlation'
    corr_df = pd.DataFrame([
        {
            'descriptor': col,
            'correlation': corr,
            'abs_correlation': abs(corr)
        }
        for col, corr in correlations.items()
    ])
    
    # Sort by absolute correlation (descending) for easier analysis
    corr_df = corr_df.sort_values('abs_correlation', ascending=False)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write to CSV
    corr_df.to_csv(output_path, index=False)
    logger.info(f"Correlation matrix written to {output_path}")
    logger.info(f"Top 5 correlated descriptors: {corr_df.head(5)['descriptor'].tolist()}")
    logger.info(f"Bottom 5 correlated descriptors: {corr_df.tail(5)['descriptor'].tolist()}")

def main():
    """Main entry point for the correlation computation script."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / "data" / "processed" / "descriptors.parquet"
    output_path = project_root / "data" / "processed" / "correlation_matrix.csv"
    
    logger.info("Starting T014b: Compute Pearson correlation matrix")
    
    try:
        compute_correlation_matrix(str(input_path), str(output_path))
        logger.info("T014b completed successfully")
    except Exception as e:
        logger.error(f"T014b failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()