import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import pandas as pd
import numpy as np

from utils.config import get_processed_path, get_random_seed, get_pseudocount
from utils.logging_config import get_logger, log_exclusion_count, log_sample_size

logger = get_logger(__name__)

def load_filtered_data() -> pd.DataFrame:
    """Load the filtered dataset from data/processed/cleared_with_diversity.csv."""
    input_path = get_processed_path("cleared_with_diversity.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def identify_zero_variance_taxa(df: pd.DataFrame) -> List[str]:
    """Identify taxa columns with zero variance (constant values)."""
    # Identify taxon columns (assume they start with 'taxon_' or are numeric columns not in metadata)
    # Based on schema, taxon columns are numeric and not subject_id, titer_baseline, titer_post
    metadata_cols = ['subject_id', 'titer_baseline', 'titer_post']
    taxon_cols = [col for col in df.columns if col not in metadata_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    zero_var_taxa = []
    for col in taxon_cols:
        if df[col].var() == 0:
            zero_var_taxa.append(col)
    
    if zero_var_taxa:
        logger.warning(f"Identified {len(zero_var_taxa)} zero-variance taxa: {zero_var_taxa}")
    return zero_var_taxa

def exclude_zero_variance_taxa(df: pd.DataFrame, zero_var_taxa: List[str]) -> pd.DataFrame:
    """Exclude zero-variance taxa from the dataset."""
    if not zero_var_taxa:
        return df
    
    excluded_df = df.drop(columns=zero_var_taxa)
    logger.info(f"Excluded {len(zero_var_taxa)} zero-variance taxa. Remaining columns: {len(excluded_df.columns)}")
    return excluded_df

def run_zero_variance_exclusion() -> pd.DataFrame:
    """Main function to run zero-variance exclusion."""
    df = load_filtered_data()
    zero_var_taxa = identify_zero_variance_taxa(df)
    df_clean = exclude_zero_variance_taxa(df, zero_var_taxa)
    
    output_path = get_processed_path("cleared_with_diversity.csv")
    df_clean.to_csv(output_path, index=False)
    logger.info(f"Saved zero-variance excluded data to {output_path}")
    return df_clean

def apply_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert absolute abundances to relative abundances (proportions).
    Sum abundances per subject and divide each taxon by the sum.
    """
    # Identify taxon columns
    metadata_cols = ['subject_id', 'titer_baseline', 'titer_post']
    taxon_cols = [col for col in df.columns if col not in metadata_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    if not taxon_cols:
        logger.warning("No taxon columns found for normalization.")
        return df
    
    # Calculate sum per row (subject)
    row_sums = df[taxon_cols].sum(axis=1)
    
    # Handle zero sums (shouldn't happen with real data, but safeguard)
    zero_sum_mask = row_sums == 0
    if zero_sum_mask.any():
        logger.warning(f"Found {zero_sum_mask.sum()} subjects with zero total abundance. Setting to NaN.")
    
    # Normalize
    normalized_df = df.copy()
    for col in taxon_cols:
        normalized_df[col] = df[col] / row_sums
    
    logger.info(f"Applied relative abundance normalization to {len(taxon_cols)} taxa.")
    return normalized_df

def apply_clr_transformation(df: pd.DataFrame, pseudocount: Optional[float] = None) -> pd.DataFrame:
    """
    Apply Centered Log Ratio (CLR) transformation.
    1. Add pseudocount to handle zeros.
    2. Calculate log(x + pseudocount).
    3. Subtract mean of logs for each row.
    """
    if pseudocount is None:
        pseudocount = get_pseudocount()
    
    logger.info(f"Applying CLR transformation with pseudocount={pseudocount}")
    
    # Identify taxon columns
    metadata_cols = ['subject_id', 'titer_baseline', 'titer_post']
    taxon_cols = [col for col in df.columns if col not in metadata_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    if not taxon_cols:
        raise ValueError("No taxon columns found for CLR transformation.")
    
    # Apply pseudocount
    df_clr = df.copy()
    df_clr[taxon_cols] = df_clr[taxon_cols].add(pseudocount)
    
    # Calculate log
    df_log = np.log(df_clr[taxon_cols])
    
    # Calculate row-wise mean
    row_means = df_log.mean(axis=1)
    
    # Subtract mean (CLR)
    for i, col in enumerate(taxon_cols):
        df_clr[col] = df_log.iloc[:, i] - row_means
    
    logger.info(f"CLR transformation complete. Added columns for {len(taxon_cols)} taxa.")
    return df_clr

def run_clr_transformation() -> pd.DataFrame:
    """Main function to run CLR transformation."""
    df = load_filtered_data()
    df_clr = apply_clr_transformation(df)
    
    output_path = get_processed_path("cleared_with_diversity.csv")
    df_clr.to_csv(output_path, index=False)
    logger.info(f"Saved CLR transformed data to {output_path}")
    return df_clr

def calculate_shannon_diversity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Shannon diversity index for each subject.
    H = -sum(p_i * ln(p_i))
    """
    # Identify taxon columns
    metadata_cols = ['subject_id', 'titer_baseline', 'titer_post']
    taxon_cols = [col for col in df.columns if col not in metadata_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    if not taxon_cols:
        logger.warning("No taxon columns found for Shannon diversity calculation.")
        return df
    
    # Ensure data is normalized (relative abundance)
    # If not, normalize first
    row_sums = df[taxon_cols].sum(axis=1)
    if not np.allclose(row_sums, 1.0, atol=1e-3):
        logger.info("Data not normalized. Normalizing before Shannon calculation.")
        df = apply_normalization(df)
    
    # Calculate Shannon index
    df_shannon = df.copy()
    p = df_shannon[taxon_cols]
    # Handle zeros: p * ln(p) is 0 when p is 0
    with np.errstate(divide='ignore', invalid='ignore'):
        log_p = np.log(p)
        log_p[p == 0] = 0
    
    shannon = -1 * (p * log_p).sum(axis=1)
    df_shannon['shannon_diversity'] = shannon
    
    logger.info(f"Calculated Shannon diversity for {len(df_shannon)} subjects.")
    return df_shannon

def log_titer_statistics(df: pd.DataFrame) -> None:
    """Log statistics for titer columns."""
    if 'titer_post' in df.columns:
        logger.info(f"Titer post stats: mean={df['titer_post'].mean():.2f}, std={df['titer_post'].std():.2f}")
    if 'titer_baseline' in df.columns:
        logger.info(f"Titer baseline stats: mean={df['titer_baseline'].mean():.2f}, std={df['titer_baseline'].std():.2f}")

def run_titer_log_transformation() -> pd.DataFrame:
    """
    Apply log transformation to titer_post.
    Handles LOD (Limit of Detection) by imputing 0.5 * LOD for values < LOD.
    """
    df = load_filtered_data()
    
    # Assume LOD is defined in config or use a default (e.g., 10)
    # For this implementation, we'll use a default LOD of 10 if not specified
    LOD = 10.0
    
    if 'titer_post' in df.columns:
        # Impute values < LOD
        imputed_count = (df['titer_post'] < LOD).sum()
        if imputed_count > 0:
            logger.info(f"Imputing {imputed_count} titer values < LOD ({LOD}) with 0.5 * LOD")
            df.loc[df['titer_post'] < LOD, 'titer_post'] = 0.5 * LOD
        
        # Apply log transformation: log(titer + 1) to handle potential zeros after imputation
        df['log_titer'] = np.log(df['titer_post'] + 1)
        logger.info("Applied log transformation to titer_post, created 'log_titer' column.")
    else:
        logger.warning("titer_post column not found, skipping log transformation.")
    
    return df

def main():
    """Main entry point for preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline.")
    
    # 1. Zero-variance exclusion (T019)
    df = run_zero_variance_exclusion()
    
    # 2. Normalization (T019a) - THIS TASK
    df_norm = apply_normalization(df)
    output_path = get_processed_path("cleared_with_diversity.csv")
    df_norm.to_csv(output_path, index=False)
    logger.info(f"Task T019a Complete: Normalization saved to {output_path}")
    
    # 3. CLR transformation (T020a)
    df_clr = apply_clr_transformation(df_norm)
    df_clr.to_csv(output_path, index=False)
    logger.info(f"Task T020a Complete: CLR saved to {output_path}")
    
    # 4. Log titer transformation (T021)
    df_final = run_titer_log_transformation()
    df_final.to_csv(output_path, index=False)
    logger.info(f"Task T021 Complete: Log titers saved to {output_path}")
    
    # 5. Shannon diversity (T020c)
    df_final = calculate_shannon_diversity(df_final)
    df_final.to_csv(output_path, index=False)
    logger.info(f"Task T020c Complete: Shannon diversity saved to {output_path}")
    
    logger.info("Preprocessing pipeline finished.")
    return df_final

if __name__ == "__main__":
    main()