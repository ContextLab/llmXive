import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import pandas as pd
import numpy as np

from utils.config import get_pseudocount, get_min_sample_size, get_use_synthetic_data
from utils.logging_config import get_logger, log_error_context
from utils.validators import validate_dataframe_not_empty

logger = get_logger(__name__)

def load_filtered_data(input_path: Path) -> pd.DataFrame:
    """Load the merged and filtered dataset from T011d."""
    logger.info(f"Loading filtered data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    validate_dataframe_not_empty(df, "Input dataset")
    
    # Ensure titer columns are numeric
    for col in ['titer_baseline', 'titer_post']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def normalize_to_relative_abundance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize OTU counts to relative abundance (sum to 1 per subject).
    Operates on all columns except 'subject_id', 'titer_baseline', 'titer_post'.
    """
    logger.info("Normalizing to relative abundance...")
    df_norm = df.copy()
    
    # Identify taxon columns (exclude metadata)
    exclude_cols = ['subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity']
    # Also exclude any CLR columns if they already exist (though they shouldn't at this stage)
    existing_clr_cols = [c for c in df.columns if c.endswith('_clr')]
    exclude_cols.extend(existing_clr_cols)
    
    taxon_cols = [c for c in df.columns if c not in exclude_cols]
    
    if not taxon_cols:
        raise ValueError("No taxon columns found for normalization.")
    
    # Calculate sum per row
    row_sums = df_norm[taxon_cols].sum(axis=1)
    
    # Avoid division by zero
    row_sums = row_sums.replace(0, np.nan)
    
    for col in taxon_cols:
        df_norm[col] = df_norm[col] / row_sums
    
    # Replace NaN (from 0/0) with 0
    df_norm[taxon_cols] = df_norm[taxon_cols].fillna(0)
    
    logger.info(f"Normalized {len(taxon_cols)} taxa columns.")
    return df_norm

def calculate_shannon_diversity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Shannon Diversity Index for each subject based on normalized abundances.
    Formula: H = -sum(p * ln(p)) for p > 0
    """
    logger.info("Calculating Shannon diversity...")
    df_div = df.copy()
    
    # Identify taxon columns (normalized)
    exclude_cols = ['subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity']
    existing_clr_cols = [c for c in df.columns if c.endswith('_clr')]
    exclude_cols.extend(existing_clr_cols)
    
    taxon_cols = [c for c in df.columns if c not in exclude_cols]
    
    if not taxon_cols:
        raise ValueError("No taxon columns found for diversity calculation.")
    
    def shannon(row):
        # Filter out zeros to avoid log(0)
        p = row[taxon_cols]
        p = p[p > 0]
        if len(p) == 0:
            return 0.0
        return -np.sum(p * np.log(p))
    
    df_div['shannon_diversity'] = df_div.apply(shannon, axis=1)
    logger.info("Shannon diversity calculated.")
    return df_div

def apply_log_titer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply log10 transformation to titer_post.
    Handles zero or negative values by adding a small pseudocount if necessary,
    though biologically titers are usually >= 1.
    """
    logger.info("Applying log transform to titer_post...")
    df_log = df.copy()
    
    if 'titer_post' not in df_log.columns:
        raise ValueError("titer_post column not found.")
    
    # Ensure numeric
    df_log['titer_post'] = pd.to_numeric(df_log['titer_post'], errors='coerce')
    
    # Handle zeros/negatives by replacing with a small positive value before log
    # Assuming min meaningful titer is 1, so we use 1e-6 for 0 to avoid log(0)
    # But typically titers are >= 10 or similar. Let's be safe.
    min_val = df_log['titer_post'].min()
    if min_val <= 0:
        logger.warning(f"Found titers <= 0 (min={min_val}). Adding pseudocount of 1e-6.")
        df_log['titer_post'] = df_log['titer_post'].replace(0, 1e-6)
        df_log['titer_post'] = df_log['titer_post'].clip(lower=1e-6)
    
    df_log['log_titer'] = np.log10(df_log['titer_post'])
    logger.info("Log transform applied.")
    return df_log

def apply_clr_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Centered Log Ratio (CLR) transformation to taxon abundances.
    1. Replace zeros with a pseudocount.
    2. Calculate geometric mean of each row.
    3. CLR(x) = ln(x / g) where g is the geometric mean.
    """
    logger.info("Applying CLR transformation...")
    df_clr = df.copy()
    
    pseudocount = get_pseudocount()
    
    # Identify taxon columns (normalized, non-CLR)
    exclude_cols = ['subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity']
    existing_clr_cols = [c for c in df.columns if c.endswith('_clr')]
    exclude_cols.extend(existing_clr_cols)
    
    taxon_cols = [c for c in df.columns if c not in exclude_cols]
    
    if not taxon_cols:
        raise ValueError("No taxon columns found for CLR transformation.")
    
    # Add pseudocount to handle zeros
    df_clr[taxon_cols] = df_clr[taxon_cols].add(pseudocount)
    
    # Calculate geometric mean per row
    # GM = exp(mean(log(x)))
    log_data = np.log(df_clr[taxon_cols])
    geo_mean = np.exp(log_data.mean(axis=1))
    
    # Apply CLR
    for col in taxon_cols:
        clr_col_name = f"{col}_clr"
        df_clr[clr_col_name] = np.log(df_clr[col] / geo_mean)
    
    logger.info(f"CLR transformation applied to {len(taxon_cols)} taxa. New columns: {[f'{c}_clr' for c in taxon_cols]}")
    return df_clr

def run_preprocessing_pipeline(input_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Execute the full preprocessing chain:
    1. Load data
    2. Normalize to relative abundance
    3. Calculate Shannon diversity
    4. Log-transform titer_post
    5. Apply CLR transformation
    6. Save to output
    """
    logger.info("Starting preprocessing pipeline...")
    
    # Step 1: Load
    df = load_filtered_data(input_path)
    
    # Step 2: Normalize
    df = normalize_to_relative_abundance(df)
    
    # Step 3: Diversity
    df = calculate_shannon_diversity(df)
    
    # Step 4: Log Titer
    df = apply_log_titer(df)
    
    # Step 5: CLR
    df = apply_clr_transformation(df)
    
    # Step 6: Save
    logger.info(f"Saving processed data to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info("Preprocessing pipeline completed successfully.")
    
    return df

def main():
    """Main entry point for T011e."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / "data" / "processed" / "cleared_with_diversity.csv"
    output_path = project_root / "data" / "processed" / "cleared_with_diversity.csv"
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        run_preprocessing_pipeline(input_path, output_path)
        logger.info("Task T011e completed successfully.")
    except Exception as e:
        logger.error(f"Task T011e failed: {e}")
        log_error_context(e)
        sys.exit(1)

if __name__ == "__main__":
    main()