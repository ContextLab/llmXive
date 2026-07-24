import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import pandas as pd
import numpy as np
from scipy.stats import entropy

from utils.config import get_processed_path, get_random_seed
from utils.logging_config import get_logger, log_sample_size

# Configure logger
logger = get_logger(__name__)

def load_filtered_data() -> pd.DataFrame:
    """Load the filtered dataset from the processed directory."""
    input_path = get_processed_path("filtered_no_zero_var.csv")
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T019 (zero-variance exclusion) has completed successfully."
        )
    logger.info(f"Loading filtered data from {input_path}")
    df = pd.read_csv(input_path)
    return df

def identify_zero_variance_taxa(df: pd.DataFrame) -> List[str]:
    """Identify taxa columns with zero variance."""
    # Assuming subject_id is the first column, and titers are separate
    # Taxa columns are numeric columns excluding subject_id and titer columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    titer_cols = [c for c in numeric_cols if 'titer' in c.lower()]
    taxa_cols = [c for c in numeric_cols if c not in titer_cols]

    zero_var_taxa = []
    for col in taxa_cols:
        if df[col].var() == 0:
            zero_var_taxa.append(col)
    
    logger.info(f"Identified {len(zero_var_taxa)} zero-variance taxa: {zero_var_taxa}")
    return zero_var_taxa

def exclude_zero_variance_taxa(df: pd.DataFrame, zero_var_taxa: List[str]) -> pd.DataFrame:
    """Exclude zero-variance taxa from the dataframe."""
    if not zero_var_taxa:
        return df
    
    df_clean = df.drop(columns=zero_var_taxa)
    logger.info(f"Excluded {len(zero_var_taxa)} zero-variance taxa. Remaining taxa: {len(df_clean.select_dtypes(include=[np.number]).columns) - len([c for c in df_clean.columns if 'titer' in c.lower()])}")
    return df_clean

def apply_clr_transformation(df: pd.DataFrame, pseudocount: float = 1e-6) -> pd.DataFrame:
    """Apply Centered Log-Ratio (CLR) transformation to taxa abundances."""
    # Identify taxa columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    titer_cols = [c for c in numeric_cols if 'titer' in c.lower()]
    subject_col = [c for c in df.columns if c == 'subject_id']
    taxa_cols = [c for c in numeric_cols if c not in titer_cols and c not in subject_col]

    if not taxa_cols:
        logger.warning("No taxa columns found for CLR transformation.")
        return df

    df_clr = df.copy()
    
    # Add pseudocount to handle zeros
    df_clr[taxa_cols] = df_clr[taxa_cols] + pseudocount

    # Calculate geometric mean for each row
    geometric_mean = np.exp(np.mean(np.log(df_clr[taxa_cols]), axis=1))

    # Apply CLR: log(x / geometric_mean)
    for col in taxa_cols:
        df_clr[col] = np.log(df_clr[col] / geometric_mean)

    logger.info(f"Applied CLR transformation with pseudocount={pseudocount} to {len(taxa_cols)} taxa.")
    return df_clr

def calculate_shannon_diversity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Shannon diversity index for each subject.
    
    Input: DataFrame with relative abundances (before CLR).
    Output: DataFrame with an additional 'shannon_diversity' column.
    """
    # Identify taxa columns (relative abundances)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    titer_cols = [c for c in numeric_cols if 'titer' in c.lower()]
    subject_col = [c for c in df.columns if c == 'subject_id']
    taxa_cols = [c for c in numeric_cols if c not in titer_cols and c not in subject_col]

    if not taxa_cols:
        raise ValueError("No taxa columns found to calculate Shannon diversity.")

    logger.info(f"Calculating Shannon diversity for {len(taxa_cols)} taxa.")

    # Shannon diversity: H = -sum(p * ln(p))
    # p is the relative abundance of each taxon
    # Ensure we are working with relative abundances (sum to 1 per row)
    # If the input is already relative abundances, we can proceed directly.
    # If not, we normalize.
    row_sums = df[taxa_cols].sum(axis=1)
    
    # Check if already normalized (sum ~ 1)
    if not np.allclose(row_sums, 1.0, rtol=1e-3):
        logger.warning("Input abundances do not sum to 1. Normalizing to relative abundances.")
        df_normalized = df[taxa_cols].div(row_sums, axis=0)
    else:
        df_normalized = df[taxa_cols]

    # Handle zeros: Shannon diversity is undefined for p=0, so we only sum where p > 0
    # p * ln(p) is 0 when p is 0 (limit as p->0)
    # We use np.where to avoid log(0)
    log_p = np.where(df_normalized > 0, np.log(df_normalized), 0)
    shannon_div = -np.sum(df_normalized * log_p, axis=1)

    # Create a copy and add the new column
    df_out = df.copy()
    df_out['shannon_diversity'] = shannon_div

    logger.info(f"Calculated Shannon diversity. Range: [{shannon_div.min():.4f}, {shannon_div.max():.4f}]")
    return df_out

def run_zero_variance_exclusion() -> Tuple[pd.DataFrame, List[str]]:
    """Main function to run zero-variance exclusion."""
    df = load_filtered_data()
    zero_var_taxa = identify_zero_variance_taxa(df)
    df_clean = exclude_zero_variance_taxa(df, zero_var_taxa)
    
    output_path = get_processed_path("filtered_no_zero_var.csv")
    df_clean.to_csv(output_path, index=False)
    logger.info(f"Saved zero-variance excluded data to {output_path}")
    
    return df_clean, zero_var_taxa

def run_clr_transformation(pseudocount: float = 1e-6) -> pd.DataFrame:
    """Main function to run CLR transformation."""
    # Load the data that has already had zero-variance taxa excluded
    input_path = get_processed_path("filtered_no_zero_var.csv")
    if not input_path.exists():
        # If not exists, run the exclusion first
        df, _ = run_zero_variance_exclusion()
    else:
        df = pd.read_csv(input_path)

    df_clr = apply_clr_transformation(df, pseudocount)
    
    output_path = get_processed_path(f"cleared_default.csv" if pseudocount == 1e-6 else f"cleared_pseudocount_{pseudocount}.csv")
    df_clr.to_csv(output_path, index=False)
    logger.info(f"Saved CLR transformed data to {output_path}")
    
    return df_clr

def run_shannon_diversity_calculation() -> pd.DataFrame:
    """
    Main function to calculate Shannon diversity and append to the dataset.
    
    This function:
    1. Loads data from data/processed/filtered_no_zero_var.csv (relative abundances, BEFORE CLR).
    2. Calculates Shannon diversity index.
    3. Appends the 'shannon_diversity' column.
    4. Saves to data/processed/cleared_with_diversity.csv.
    """
    logger.info("Starting Shannon diversity calculation (Task T020c).")
    
    # Load input: filtered_no_zero_var.csv
    input_path = get_processed_path("filtered_no_zero_var.csv")
    if not input_path.exists():
        # If the zero-variance exclusion hasn't been run, run it now
        logger.warning("Input file filtered_no_zero_var.csv not found. Running zero-variance exclusion first.")
        df, _ = run_zero_variance_exclusion()
    else:
        logger.info(f"Loading input from {input_path}")
        df = pd.read_csv(input_path)

    # Calculate Shannon diversity
    df_with_diversity = calculate_shannon_diversity(df)

    # Save output
    output_path = get_processed_path("cleared_with_diversity.csv")
    df_with_diversity.to_csv(output_path, index=False)
    
    logger.info(f"Saved dataset with Shannon diversity to {output_path}")
    log_sample_size(len(df_with_diversity), "Shannon diversity calculation")
    
    return df_with_diversity

def log_titer_statistics(df: pd.DataFrame) -> None:
    """Log statistics for titer columns."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    titer_cols = [c for c in numeric_cols if 'titer' in c.lower()]
    
    for col in titer_cols:
        logger.info(f"Titer column '{col}': mean={df[col].mean():.2f}, std={df[col].std():.2f}, min={df[col].min():.2f}, max={df[col].max():.2f}")

def run_titer_log_transformation() -> pd.DataFrame:
    """Apply log transformation to titer columns."""
    input_path = get_processed_path("cleared_with_diversity.csv")
    if not input_path.exists():
        # Run Shannon diversity first if not done
        df = run_shannon_diversity_calculation()
    else:
        df = pd.read_csv(input_path)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    titer_cols = [c for c in numeric_cols if 'titer' in c.lower()]

    df_log = df.copy()
    for col in titer_cols:
        # Add small constant to avoid log(0)
        df_log[col] = np.log1p(df_log[col])
    
    output_path = get_processed_path("cleared_with_diversity_log_titers.csv")
    df_log.to_csv(output_path, index=False)
    logger.info(f"Saved log-transformed titer data to {output_path}")
    
    return df_log

def main():
    """Entry point for the preprocessing module."""
    # Run Shannon diversity calculation as per T020c
    run_shannon_diversity_calculation()
    
    # Optionally run CLR transformation (T020) if needed
    # run_clr_transformation()
    
    # Optionally run titer log transformation (T021)
    # run_titer_log_transformation()

if __name__ == "__main__":
    main()
