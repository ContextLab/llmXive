import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Optional

import pandas as pd
import numpy as np

from utils.config import get_pseudocount, get_processed_path, get_research_path
from utils.logging_config import get_logger

logger = get_logger(__name__)


def load_cleared_data(filepath: Path) -> pd.DataFrame:
    """
    Load a CSV dataset from disk.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    return df


def identify_taxa_columns(df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> List[str]:
    """
    Identify columns representing taxa abundances.
    Excludes standard metadata columns and specified exclude_cols.
    """
    default_exclude = ['subject_id', 'titer_baseline', 'titer_post',
                       'titer_pre_log', 'titer_post_log', 'shannon_diversity',
                       'log_titer']
    if exclude_cols:
        default_exclude.extend(exclude_cols)

    taxa_cols = [col for col in df.columns if col not in default_exclude]
    logger.info(f"Identified {len(taxa_cols)} taxa columns: {taxa_cols}")
    return taxa_cols


def apply_clr_transformation(df: pd.DataFrame, taxa_cols: List[str], pseudocount: float) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to the specified taxa columns.
    
    1. Add a small pseudo-count to all zero abundances to handle log(0).
    2. Calculate the geometric mean of the abundances for each sample (row).
    3. Compute the CLR: ln(abundance / geometric_mean).
    
    Returns a DataFrame with the original columns plus new CLR columns.
    """
    if len(taxa_cols) == 0:
        logger.warning("No taxa columns provided for CLR transformation.")
        return df

    # Create a copy to avoid modifying the original
    df_clr = df.copy()
    
    # Select the abundance matrix
    X = df_clr[taxa_cols].astype(float)
    
    # 1. Zero Replacement
    # Add pseudocount to all values in the selected columns
    X = X + pseudocount
    
    # 2. Geometric Mean Calculation
    # Geometric mean is the exp(mean(log(x)))
    # We use log on the pseudocount-adjusted values
    log_X = np.log(X)
    geo_mean_log = log_X.mean(axis=1)
    
    # 3. CLR Calculation: ln(x_i / G) = ln(x_i) - ln(G)
    # Since geo_mean_log is ln(G), we subtract it from ln(x_i)
    clr_matrix = log_X - geo_mean_log.values[:, np.newaxis]
    
    # Create column names for the CLR results
    clr_cols = [f"{col}_clr" for col in taxa_cols]
    clr_df = pd.DataFrame(clr_matrix, columns=clr_cols, index=df_clr.index)
    
    # Concatenate the CLR columns to the original dataframe
    df_result = pd.concat([df_clr, clr_df], axis=1)
    
    logger.info(f"CLR transformation complete. Added {len(clr_cols)} new columns.")
    return df_result


def write_updated_dataset(df: pd.DataFrame, filepath: Path) -> None:
    """
    Write the processed DataFrame to a CSV file.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False)
    logger.info(f"Dataset written to {filepath}")


def run_clr_pipeline() -> None:
    """
    Orchestrates the CLR transformation pipeline.
    
    Inputs:
      - data/processed/cleared_shannon.csv
      - data/processed/cleared_log.csv
      - data/processed/cleared_norm.csv
    
    Output:
      - data/processed/cleared_final.csv
    """
    processed_path = get_processed_path()
    
    file_shannon = processed_path / "cleared_shannon.csv"
    file_log = processed_path / "cleared_log.csv"
    file_norm = processed_path / "cleared_norm.csv"
    file_output = processed_path / "cleared_final.csv"
    
    logger.info("Starting CLR Pipeline (T020a)")
    
    # 1. Load Inputs
    try:
        df_shannon = load_cleared_data(file_shannon)
        df_log = load_cleared_data(file_log)
        df_norm = load_cleared_data(file_norm)
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    
    # 2. Verify Alignment
    logger.info("Verifying subject alignment across inputs...")
    subjects_shannon = set(df_shannon['subject_id'])
    subjects_log = set(df_log['subject_id'])
    subjects_norm = set(df_norm['subject_id'])
    
    if subjects_shannon != subjects_log or subjects_shannon != subjects_norm:
        msg = "Subject ID mismatch between input files. Cannot proceed."
        logger.error(msg)
        raise ValueError(msg)
    
    if not (len(df_shannon) == len(df_log) == len(df_norm)):
        msg = f"Row count mismatch: Shannon={len(df_shannon)}, Log={len(df_log)}, Norm={len(df_norm)}"
        logger.error(msg)
        raise ValueError(msg)
    
    # 3. Merge Inputs
    # We merge on subject_id. Since sets are identical, an inner join is safe and sufficient.
    df_merged = pd.merge(df_shannon, df_log, on='subject_id', suffixes=('_sh', '_lg'))
    df_merged = pd.merge(df_merged, df_norm, on='subject_id', suffixes=('', '_nm'))
    
    # Clean up potential duplicate columns if any (e.g. if log_titer was in both)
    # We expect unique columns now, but let's ensure subject_id is unique
    if df_merged.columns.duplicated().any():
        logger.warning("Duplicate columns found after merge. Dropping duplicates.")
        df_merged = df_merged.loc[:, ~df_merged.columns.duplicated()]
    
    logger.info(f"Merged dataset shape: {df_merged.shape}")
    
    # 4. Identify Taxa Columns (from the normalized data part of the merge)
    # We look for columns that are in the normalized set but not in metadata
    # Assuming the normalized data columns are the ones ending in _nm or just the raw taxon names if not suffixed
    # To be safe, we identify taxa columns from df_norm specifically, then map them to df_merged
    taxa_cols = identify_taxa_columns(df_norm)
    
    # Map original names to merged names if suffixes were applied
    # In the merge above, we used suffixes for 'cleared_shannon' and 'cleared_log' but not for 'cleared_norm'
    # Wait, the merge logic:
    # merge(shannon, log) -> suffixes _sh, _lg
    # merge(result, norm) -> suffixes '', '_nm' (default is _x, _y, but we passed suffixes=('', '_nm')? No, we didn't pass suffixes for the second merge)
    # Actually, pd.merge default suffixes are ('_x', '_y').
    # Let's rely on the fact that norm columns are the ones we want for CLR.
    # We need to find the corresponding columns in df_merged.
    
    # Re-identify taxa columns in the merged dataframe based on the names from df_norm
    # The merge might have added suffixes if there were overlapping column names between (shannon+log) and norm.
    # Common overlap: subject_id (handled by merge key).
    # If norm has 'taxon_0', and shannon/log don't, it stays 'taxon_0'.
    # If norm has 'titer_baseline' (unlikely), it might get a suffix.
    # We assume taxon columns are unique to the norm file.
    
    final_taxa_cols = []
    for col in taxa_cols:
        if col in df_merged.columns:
            final_taxa_cols.append(col)
        elif f"{col}_nm" in df_merged.columns:
            final_taxa_cols.append(f"{col}_nm")
        else:
            # Check for default suffixes
            if f"{col}_x" in df_merged.columns:
                final_taxa_cols.append(f"{col}_x")
            elif f"{col}_y" in df_merged.columns:
                final_taxa_cols.append(f"{col}_y")
    
    if len(final_taxa_cols) != len(taxa_cols):
        logger.warning(f"Could not find all taxa columns in merged data. Expected {len(taxa_cols)}, found {len(final_taxa_cols)}.")
        # We proceed with what we found, but log a warning.
    
    if len(final_taxa_cols) == 0:
        logger.error("No taxa columns found in the merged dataset for CLR transformation.")
        raise ValueError("No taxa columns found.")
    
    # 5. Apply CLR
    pseudocount = get_pseudocount()
    logger.info(f"Applying CLR with pseudocount: {pseudocount}")
    df_final = apply_clr_transformation(df_merged, final_taxa_cols, pseudocount)
    
    # 6. Write Output
    write_updated_dataset(df_final, file_output)
    logger.info("CLR Pipeline completed successfully.")


def main():
    """
    Entry point for the script.
    """
    try:
        run_clr_pipeline()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()