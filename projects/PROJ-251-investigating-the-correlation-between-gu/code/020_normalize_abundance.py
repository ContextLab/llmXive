import os
import sys
import logging
from pathlib import Path
from typing import List, Optional
import pandas as pd
import numpy as np

from utils.logging_config import get_logger
from utils.config import get_raw_path, get_processed_path

logger = get_logger(__name__)

def load_merged_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the cleared dataset from the previous step (T011d).
    """
    if input_path is None:
        input_path = get_processed_path() / "cleared.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Ensure T011d has completed successfully.")
    
    logger.info(f"Loading merged data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df

def identify_taxa_columns(df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> List[str]:
    """
    Identify microbiome taxon columns.
    Excludes standard metadata columns and any explicitly excluded columns.
    """
    default_exclude = ['subject_id', 'titer_baseline', 'titer_post', 
                       'log_titer', 'shannon_diversity']
    if exclude_cols:
        default_exclude.extend(exclude_cols)
    
    # Filter out columns that are in the default exclude list
    taxa_cols = [col for col in df.columns if col not in default_exclude]
    
    # Ensure we only keep numeric columns (taxa abundances should be numeric)
    numeric_taxa_cols = [col for col in taxa_cols if pd.api.types.is_numeric_dtype(df[col])]
    
    if not numeric_taxa_cols:
        raise ValueError("No taxon columns found in the dataset. "
                         "Ensure the dataset contains numeric abundance columns.")
    
    logger.info(f"Identified {len(numeric_taxa_cols)} taxon columns: {numeric_taxa_cols[:5]}...")
    return numeric_taxa_cols

def normalize_to_relative_abundance(df: pd.DataFrame, taxa_cols: List[str]) -> pd.DataFrame:
    """
    Normalize microbiome data to relative abundance (sum = 1 per subject).
    
    For each row, divides each taxon abundance by the row sum of all taxon abundances.
    """
    df_norm = df.copy()
    
    # Calculate row sums for taxon columns
    row_sums = df_norm[taxa_cols].sum(axis=1)
    
    # Handle potential zero-sum rows (though unlikely in real data after filtering)
    zero_sum_mask = row_sums == 0
    if zero_sum_mask.any():
        logger.warning(f"Found {zero_sum_mask.sum()} rows with zero total abundance. "
                       "These rows will be excluded from normalization.")
        # For zero-sum rows, we cannot normalize. We'll set them to NaN or drop them.
        # Here we set to NaN to flag them for downstream handling.
        df_norm.loc[zero_sum_mask, taxa_cols] = np.nan
        # Update row_sums to avoid division by zero
        row_sums = row_sums.replace(0, np.nan)
    
    # Normalize: divide each taxon by its row sum
    df_norm[taxa_cols] = df_norm[taxa_cols].div(row_sums, axis=0)
    
    # Verification: Check that row sums are approximately 1.0 (for non-zero rows)
    normalized_sums = df_norm[taxa_cols].sum(axis=1)
    # Check only non-NaN sums
    valid_sums = normalized_sums.dropna()
    if len(valid_sums) > 0:
        assert np.allclose(valid_sums, 1.0, atol=1e-10), \
            f"Normalization failed: row sums are not 1.0. Min: {valid_sums.min()}, Max: {valid_sums.max()}"
    
    logger.info("Normalization complete: all taxon row sums equal 1.0 (within tolerance)")
    return df_norm

def write_updated_dataset(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Write the normalized dataset to disk.
    """
    if output_path is None:
        output_path = get_processed_path() / "cleared_norm.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Normalized dataset written to {output_path}")
    return output_path

def run_normalization_pipeline(input_path: Optional[Path] = None, 
                               output_path: Optional[Path] = None) -> Path:
    """
    Run the full normalization pipeline:
    1. Load merged data
    2. Identify taxon columns
    3. Normalize to relative abundance
    4. Write output
    """
    logger.info("Starting relative abundance normalization pipeline")
    
    # Step 1: Load data
    df = load_merged_data(input_path)
    
    # Step 2: Identify taxon columns
    taxa_cols = identify_taxa_columns(df)
    
    # Step 3: Normalize
    df_norm = normalize_to_relative_abundance(df, taxa_cols)
    
    # Step 4: Write output
    output_path = write_updated_dataset(df_norm, output_path)
    
    logger.info("Normalization pipeline completed successfully")
    return output_path

def main():
    """
    Entry point for the normalization script.
    """
    logger.info("Running 020_normalize_abundance.py")
    try:
        output_path = run_normalization_pipeline()
        logger.info(f"Success! Output written to {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Normalization pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
