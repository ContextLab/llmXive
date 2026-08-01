import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import pandas as pd
import numpy as np

from utils.config import get_processed_path, get_pseudocount, get_random_seed
from utils.logging_config import get_logger, log_exclusion_count, log_sample_size
from utils.validators import validate_dataframe_not_empty

logger = get_logger(__name__)

def load_filtered_data() -> pd.DataFrame:
    """
    Load the merged dataset from data/processed/cleared_with_diversity.csv.
    This file is expected to be produced by T011d (Merge).
    """
    input_path = get_processed_path("cleared_with_diversity.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Ensure T011d (Merge) has completed successfully.")
    
    logger.info(f"Loading filtered data from {input_path}")
    df = pd.read_csv(input_path)
    
    if df.empty:
        raise ValueError("Loaded dataset is empty. Check upstream filtering logic.")
    
    validate_dataframe_not_empty(df, "cleared_with_diversity")
    return df

def identify_zero_variance_taxa(df: pd.DataFrame) -> List[str]:
    """
    Identify taxa columns (all columns except subject_id and titer columns)
    that have zero variance across all subjects.
    """
    # Identify taxon columns: exclude known non-taxon columns
    exclude_cols = ['subject_id', 'titer_baseline', 'titer_post']
    # Also exclude any columns added in previous steps if they exist
    # For now, assume any column not in exclude_cols and numeric is a taxon
    taxon_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    zero_var_taxa = []
    for col in taxon_cols:
        if df[col].var() == 0:
            zero_var_taxa.append(col)
    
    return zero_var_taxa

def exclude_zero_variance_taxa(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Remove taxa with zero variance from the dataframe.
    Returns the filtered dataframe and the list of removed taxa.
    """
    zero_var_taxa = identify_zero_variance_taxa(df)
    if zero_var_taxa:
        logger.warning(f"Excluding {len(zero_var_taxa)} zero-variance taxa: {zero_var_taxa}")
        df_filtered = df.drop(columns=zero_var_taxa)
    else:
        df_filtered = df.copy()
        logger.info("No zero-variance taxa found.")
    
    return df_filtered, zero_var_taxa

def run_zero_variance_exclusion() -> pd.DataFrame:
    """
    Main entry point for zero-variance exclusion.
    Loads data, excludes zero-variance taxa, and saves the result.
    """
    df = load_filtered_data()
    initial_count = len(df.columns)
    
    df_filtered, removed_taxa = exclude_zero_variance_taxa(df)
    
    final_count = len(df_filtered.columns)
    excluded_count = initial_count - final_count
    
    log_exclusion_count("zero_variance_taxa", excluded_count)
    
    output_path = get_processed_path("cleared_with_diversity.csv")
    df_filtered.to_csv(output_path, index=False)
    logger.info(f"Saved zero-variance excluded data to {output_path}")
    
    return df_filtered

def apply_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize OTU abundances to relative abundance (proportions) per subject.
    
    Logic:
    1. Identify taxon columns (exclude subject_id, titer_baseline, titer_post).
    2. Sum abundances per subject (row-wise sum of taxon columns).
    3. Divide each taxon abundance by the sum to get relative abundance.
    4. Return dataframe with normalized values.
    
    Input: DataFrame with absolute abundances (output of T019).
    Output: DataFrame with relative abundances (same structure, values sum to 1 per row).
    """
    # Identify taxon columns
    exclude_cols = ['subject_id', 'titer_baseline', 'titer_post']
    taxon_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    if not taxon_cols:
        raise ValueError("No taxon columns found for normalization.")
    
    # Calculate sum per subject
    row_sums = df[taxon_cols].sum(axis=1)
    
    # Handle zero-sum rows (subjects with no counts)
    if (row_sums == 0).any():
        logger.warning(f"Found {sum(row_sums == 0)} subjects with zero total counts. "
                       "These will result in NaN relative abundances.")
    
    # Normalize
    df_normalized = df.copy()
    for col in taxon_cols:
        df_normalized[col] = df[col] / row_sums
    
    # Log statistics
    logger.info(f"Normalized {len(taxon_cols)} taxa to relative abundance.")
    
    return df_normalized

def run_normalization() -> pd.DataFrame:
    """
    Main entry point for normalization.
    Loads data from T019 output, normalizes to relative abundance, and saves.
    """
    # Load the output from T019 (which is the same file path, updated by T019)
    input_path = get_processed_path("cleared_with_diversity.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Ensure T019 (Zero Variance Exclusion) has completed.")
    
    df = pd.read_csv(input_path)
    
    # Apply normalization
    df_normalized = apply_normalization(df)
    
    # Save to the SAME file path as per task requirement:
    # "Output: data/processed/cleared_with_diversity.csv"
    # The task says to update the existing file with normalized values.
    output_path = get_processed_path("cleared_with_diversity.csv")
    df_normalized.to_csv(output_path, index=False)
    
    logger.info(f"Saved normalized data to {output_path}")
    return df_normalized

def apply_clr_transformation(df: pd.DataFrame, pseudocount: Optional[float] = None) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to taxon abundances.
    
    Logic:
    1. Add pseudocount to all zero values to avoid log(0).
    2. Take natural log of all values.
    3. Subtract the geometric mean (mean of logs) per subject.
    
    Input: DataFrame with relative abundances (output of T019a).
    Output: DataFrame with CLR-transformed values.
    """
    if pseudocount is None:
        pseudocount = get_pseudocount()
    
    exclude_cols = ['subject_id', 'titer_baseline', 'titer_post']
    taxon_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    if not taxon_cols:
        raise ValueError("No taxon columns found for CLR transformation.")
    
    df_clr = df.copy()
    
    # Replace zeros with pseudocount
    df_clr[taxon_cols] = df_clr[taxon_cols].replace(0, pseudocount)
    
    # Log transform
    df_clr[taxon_cols] = np.log(df_clr[taxon_cols])
    
    # Calculate row-wise mean of logs (geometric mean in log space)
    row_means = df_clr[taxon_cols].mean(axis=1)
    
    # Subtract row mean from each taxon log value
    for col in taxon_cols:
        df_clr[col] = df_clr[col] - row_means
    
    return df_clr

def run_clr_transformation() -> pd.DataFrame:
    """
    Main entry point for CLR transformation.
    """
    input_path = get_processed_path("cleared_with_diversity.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}.")
    
    df = pd.read_csv(input_path)
    df_clr = apply_clr_transformation(df)
    
    output_path = get_processed_path("cleared_with_diversity.csv")
    df_clr.to_csv(output_path, index=False)
    
    logger.info(f"Saved CLR-transformed data to {output_path}")
    return df_clr

def calculate_shannon_diversity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Shannon diversity index for each subject.
    
    Logic:
    Shannon = - sum(p_i * ln(p_i)) for all taxa i, where p_i is relative abundance.
    
    Input: DataFrame with relative abundances.
    Output: DataFrame with added 'shannon_diversity' column.
    """
    exclude_cols = ['subject_id', 'titer_baseline', 'titer_post']
    taxon_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    if not taxon_cols:
        raise ValueError("No taxon columns found for Shannon diversity calculation.")
    
    df_shannon = df.copy()
    
    # Calculate Shannon index per row
    # Filter out zeros to avoid log(0)
    # p_i * ln(p_i) is 0 when p_i is 0 (limit)
    shannon_values = []
    for idx, row in df_shannon.iterrows():
        taxa_values = row[taxon_cols]
        # Filter non-zero values
        non_zero = taxa_values[taxa_values > 0]
        if len(non_zero) == 0:
            shannon_values.append(0.0)
        else:
            shannon = -np.sum(non_zero * np.log(non_zero))
            shannon_values.append(shannon)
    
    df_shannon['shannon_diversity'] = shannon_values
    
    return df_shannon

def log_titer_statistics(df: pd.DataFrame) -> None:
    """Log basic statistics for titer columns."""
    for col in ['titer_baseline', 'titer_post']:
        if col in df.columns:
            logger.info(f"{col} - Mean: {df[col].mean():.2f}, Median: {df[col].median():.2f}, "
                        f"Min: {df[col].min():.2f}, Max: {df[col].max():.2f}")

def run_titer_log_transformation() -> pd.DataFrame:
    """
    Apply log transformation to titer_post column.
    Handles LOD (Limit of Detection) by imputing values < LOD.
    """
    input_path = get_processed_path("cleared_with_diversity.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}.")
    
    df = pd.read_csv(input_path)
    
    # LOD handling (simplified: impute LOD/2 for values < LOD)
    # In a full implementation, LOD value would be configurable
    LOD = 10.0  # Example LOD value
    imputed_count = 0
    
    if 'titer_post' in df.columns:
        imputed_mask = df['titer_post'] < LOD
        imputed_count = imputed_mask.sum()
        if imputed_count > 0:
            logger.warning(f"Imputing {imputed_count} titer_post values < LOD ({LOD}) with LOD/2 = {LOD/2}")
            df.loc[imputed_mask, 'titer_post'] = LOD / 2
        
        # Log transform
        df['log_titer'] = np.log10(df['titer_post'])
        logger.info("Added 'log_titer' column (log10 of titer_post).")
    else:
        logger.warning("titer_post column not found. Skipping log transformation.")
    
    output_path = get_processed_path("cleared_with_diversity.csv")
    df.to_csv(output_path, index=False)
    
    return df

def main():
    """
    Main orchestration function for preprocessing pipeline.
    Executes T019 (Zero Variance), T019a (Normalization), T020a (CLR), T021 (Log Titers), T020c (Shannon).
    
    For T019a specifically:
    1. Load data from T019 output.
    2. Normalize to relative abundance.
    3. Save to data/processed/cleared_with_diversity.csv.
    """
    logger.info("Starting preprocessing pipeline.")
    
    # T019: Zero Variance Exclusion (if not already done, but task T019 is marked complete)
    # We assume T019 has run and the file exists. We re-run it to be safe or just load.
    # Per task description, T019a depends on T019. We load the T019 output.
    
    # T019a: Normalize to Relative Abundance
    logger.info("Executing T019a: Normalize to Relative Abundance.")
    df_normalized = run_normalization()
    
    # Continue with other steps if needed (CLR, Shannon, etc.)
    # But for this task, we focus on T019a output.
    
    logger.info("T019a completed successfully.")
    return df_normalized

if __name__ == "__main__":
    main()