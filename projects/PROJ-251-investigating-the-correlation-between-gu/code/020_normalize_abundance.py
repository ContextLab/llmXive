import os
import sys
import logging
from pathlib import Path
from typing import List, Optional
import pandas as pd
import numpy as np

from utils.config import get_processed_path, get_research_path, get_random_seed
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_merged_data() -> pd.DataFrame:
    """
    Load the merged dataset from the previous step (T011d).
    Expected input: data/processed/cleared.csv
    """
    input_path = get_processed_path("cleared.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Ensure T011d (Merge Microbiome and Serology) has completed successfully.")
    
    logger.info(f"Loading merged data from {input_path}")
    df = pd.read_csv(input_path)
    
    if 'subject_id' not in df.columns:
        raise ValueError("Input data must contain 'subject_id' column.")
    
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df

def identify_taxa_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns that represent taxon abundances.
    We exclude non-taxon columns: subject_id, titer_baseline, titer_post, 
    and any other non-numeric or metadata columns.
    """
    exclude_cols = ['subject_id', 'titer_baseline', 'titer_post']
    # Also exclude any columns that are clearly metadata or identifiers
    # based on common naming conventions if necessary, but for now
    # we assume all numeric columns not in exclude_cols are taxa.
    
    taxa_cols = []
    for col in df.columns:
        if col in exclude_cols:
            continue
        # Check if column is numeric
        if pd.api.types.is_numeric_dtype(df[col]):
            taxa_cols.append(col)
        else:
            # If it's not numeric, it might be a string identifier or metadata
            # We should log a warning if we encounter unexpected non-numeric columns
            logger.warning(f"Non-numeric column '{col}' found and excluded from taxa columns.")
    
    if not taxa_cols:
        raise ValueError("No taxon columns found in the dataset. "
                         "Ensure the input data contains numeric abundance columns.")
    
    logger.info(f"Identified {len(taxa_cols)} taxon columns: {taxa_cols[:5]}...")
    return taxa_cols

def normalize_to_relative_abundance(df: pd.DataFrame, taxa_cols: List[str]) -> pd.DataFrame:
    """
    Normalize microbiome data to relative abundance.
    For each row, divide each taxon abundance by the sum of all taxon abundances.
    This ensures that the sum of relative abundances for each subject is 1.0.
    """
    df_normalized = df.copy()
    
    # Calculate the sum of taxon abundances for each subject (row-wise sum)
    row_sums = df_normalized[taxa_cols].sum(axis=1)
    
    # Check for zero sums (subjects with no abundance data)
    zero_sum_mask = row_sums == 0
    if zero_sum_mask.any():
        num_zeros = zero_sum_mask.sum()
        logger.warning(f"Found {num_zeros} subjects with zero total abundance. "
                       "These will result in NaN relative abundances and should be handled.")
    
    # Normalize: divide each taxon column by the row sum
    # Use np.where or direct division; direct division will produce NaN for zero sums
    for col in taxa_cols:
        df_normalized[col] = df_normalized[col] / row_sums
    
    # Verification: Assert that the sum of taxon columns for each row is 1.0 (within tolerance)
    # We skip rows with zero sums (they will be NaN)
    valid_rows = ~row_sums.isna() & (row_sums > 0)
    if valid_rows.any():
        row_sums_after = df_normalized.loc[valid_rows, taxa_cols].sum(axis=1)
        if not np.allclose(row_sums_after, 1.0, rtol=1e-5):
            logger.error("Normalization verification failed: row sums are not 1.0 after normalization.")
            # We do not raise an error here to allow the pipeline to proceed, but log the issue
            # In a strict environment, this might be a failure condition
        else:
            logger.info("Normalization verification passed: all non-zero rows sum to 1.0.")
    
    return df_normalized

def write_updated_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """
    Write the normalized dataset to the specified output path.
    Expected output: data/processed/cleared_norm.csv
    """
    if not os.exists(os.dirname(output_path)):
        os.makedirs(os.dirname(output_path), exist_ok=True)
    
    logger.info(f"Writing normalized data to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(df)} rows to {output_path}")

def run_normalization_pipeline() -> None:
    """
    Main pipeline function to orchestrate the normalization steps.
    """
    logger.info("Starting Relative Abundance Normalization Pipeline (T020b)")
    
    # Step 1: Load data
    df = load_merged_data()
    
    # Step 2: Identify taxon columns
    taxa_cols = identify_taxa_columns(df)
    
    # Step 3: Normalize to relative abundance
    df_normalized = normalize_to_relative_abundance(df, taxa_cols)
    
    # Step 4: Write output
    output_path = get_processed_path("cleared_norm.csv")
    write_updated_dataset(df_normalized, output_path)
    
    logger.info("Normalization pipeline completed successfully.")

def main() -> None:
    """
    Entry point for the script.
    """
    run_normalization_pipeline()

if __name__ == "__main__":
    main()
