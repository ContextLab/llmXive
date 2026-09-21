"""
Shannon Diversity Calculation Task (T020c).

Calculates the Shannon diversity index from normalized microbiome data
and writes the result to a new CSV file.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Import local utilities to match project API surface
from utils.logging_config import get_logger
from utils.config import get_processed_path, get_random_seed

logger = get_logger(__name__)


def load_cleared_data(input_path: Path) -> pd.DataFrame:
    """
    Loads the normalized data from the previous step.

    Args:
        input_path: Path to 'cleared_norm.csv'

    Returns:
        DataFrame containing normalized abundances.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Validate required columns exist
    required_cols = ['subject_id', 'titer_baseline', 'titer_post']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in input: {missing}")
    
    return df


def identify_taxa_columns(df: pd.DataFrame) -> list:
    """
    Identifies columns representing microbiome taxa.
    Excludes known metadata columns and non-numeric columns.
    """
    exclude_cols = {'subject_id', 'titer_baseline', 'titer_post', 
                    'titer_pre_log', 'titer_post_log', 'shannon_diversity'}
    
    taxa_cols = []
    for col in df.columns:
        if col not in exclude_cols:
            # Check if column is numeric (abundance)
            if pd.api.types.is_numeric_dtype(df[col]):
                taxa_cols.append(col)
    
    if not taxa_cols:
        logger.warning("No numeric taxon columns found. Returning empty list.")
    
    return sorted(taxa_cols)


def calculate_shannon_diversity(df: pd.DataFrame, taxa_cols: list) -> pd.Series:
    """
    Calculates Shannon diversity index for each row.
    
    Formula: H = -sum(p_i * ln(p_i))
    where p_i is the proportion of taxon i.
    
    Args:
        df: DataFrame with abundance columns.
        taxa_cols: List of taxon column names.
        
    Returns:
        Series of Shannon diversity values.
    """
    if not taxa_cols:
        return pd.Series([0.0] * len(df), index=df.index)

    # Extract abundance matrix
    abundances = df[taxa_cols].values

    # Handle potential NaNs by filling with 0 (though normalized data should be clean)
    abundances = np.nan_to_num(abundances, nan=0.0)

    # Calculate row sums to ensure we are working with proportions (should be ~1.0)
    # If data is already normalized, this is just a safety check.
    row_sums = abundances.sum(axis=1, keepdims=True)
    
    # Avoid division by zero
    row_sums = np.where(row_sums == 0, 1.0, row_sums)
    
    # Calculate proportions
    proportions = abundances / row_sums

    # Calculate Shannon index: H = - sum(p * ln(p))
    # We use np.where to handle 0 * ln(0) which is defined as 0
    log_props = np.log(proportions)
    log_props = np.where(proportions == 0, 0.0, log_props)
    
    shannon_h = -np.sum(proportions * log_props, axis=1)

    return pd.Series(shannon_h, index=df.index, name='shannon_diversity')


def write_updated_dataset(df: pd.DataFrame, shannon_series: pd.Series, output_path: Path) -> None:
    """
    Writes the dataframe with the new Shannon diversity column to disk.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add the new column
    df_with_shannon = df.copy()
    df_with_shannon['shannon_diversity'] = shannon_series
    
    logger.info(f"Writing output to {output_path}")
    df_with_shannon.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(df_with_shannon)} rows to {output_path}")


def run_shannon_pipeline(input_path: Path, output_path: Path) -> None:
    """
    Orchestrates the Shannon diversity calculation pipeline.
    """
    logger.info("Starting Shannon Diversity Calculation (T020c)")
    
    # 1. Load Data
    df = load_cleared_data(input_path)
    
    # 2. Identify Taxa
    taxa_cols = identify_taxa_columns(df)
    logger.info(f"Identified {len(taxa_cols)} taxon columns for diversity calculation.")
    
    # 3. Calculate Shannon Index
    shannon_values = calculate_shannon_diversity(df, taxa_cols)
    
    # 4. Write Output
    write_updated_dataset(df, shannon_values, output_path)
    
    logger.info("Shannon Diversity Calculation completed successfully.")


def main():
    """
    Entry point for the script.
    """
    # Configure paths
    input_file = get_processed_path("cleared_norm.csv")
    output_file = get_processed_path("cleared_shannon.csv")
    
    # Set logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        run_shannon_pipeline(input_file, output_file)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
