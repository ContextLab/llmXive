import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import pandas as pd
import numpy as np

# Import existing utilities from the project
from utils.config import get_processed_path, get_pseudocount, get_use_synthetic_data
from utils.logging_config import get_logger, log_error_context
from utils.validators import validate_file_exists

logger = get_logger(__name__)

def load_filtered_data(file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the filtered dataset from the processed directory.
    Defaults to 'cleared_with_diversity.csv' if no path is provided.
    """
    if file_path is None:
        file_path = str(get_processed_path() / "cleared_with_diversity.csv")
    
    if not validate_file_exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    logger.info(f"Loading data from {file_path}")
    df = pd.read_csv(file_path)
    
    # Identify taxon columns (assume they start with 'taxa_' or are not known metadata columns)
    # For this implementation, we assume columns other than 'subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity' are taxa
    known_metadata = ['subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity']
    taxon_columns = [col for col in df.columns if col not in known_metadata]
    
    if len(taxon_columns) == 0:
        logger.warning("No taxon columns found in the dataset. Check column naming convention.")
    
    logger.info(f"Loaded {len(df)} rows. Found {len(taxon_columns)} taxon columns.")
    return df, taxon_columns

def apply_normalization(df: pd.DataFrame, taxon_columns: List[str]) -> pd.DataFrame:
    """
    Normalize taxon abundances to relative abundance (sum to 1 per subject).
    """
    logger.info("Applying relative abundance normalization...")
    
    # Calculate sum of abundances per row for taxon columns
    row_sums = df[taxon_columns].sum(axis=1)
    
    # Avoid division by zero
    row_sums[row_sums == 0] = np.nan
    
    for col in taxon_columns:
        df[col] = df[col] / row_sums
    
    # Fill NaN with 0 if any subject had 0 total abundance (though unlikely in real data)
    df[taxon_columns] = df[taxon_columns].fillna(0)
    
    logger.info("Normalization complete.")
    return df

def run_normalization(input_path: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """
    Run the normalization pipeline.
    """
    if input_path is None:
        input_path = str(get_processed_path() / "cleared_with_diversity.csv")
    if output_path is None:
        output_path = str(get_processed_path() / "cleared_with_diversity.csv")
    
    df, taxon_columns = load_filtered_data(input_path)
    df = apply_normalization(df, taxon_columns)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Normalized data saved to {output_path}")
    return output_path

def apply_clr_transformation(df: pd.DataFrame, taxon_columns: List[str], pseudocount: Optional[float] = None) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to taxon abundances.
    
    Steps:
    1. Replace zeros with a small pseudocount (default 1e-6).
    2. Calculate the geometric mean of abundances for each sample.
    3. Compute log(abundance / geometric_mean) for each taxon.
    
    Args:
        df: DataFrame containing the data.
        taxon_columns: List of column names representing taxa.
        pseudocount: Value to replace zeros. If None, uses config default.
    
    Returns:
        DataFrame with new CLR-transformed columns (named 'clr_{taxon}').
    """
    if pseudocount is None:
        pseudocount = get_pseudocount()
    
    logger.info(f"Applying CLR transformation with pseudocount={pseudocount}...")
    
    # Create a copy of the taxon data to avoid modifying original
    taxon_data = df[taxon_columns].copy()
    
    # Step 1: Zero replacement
    zero_mask = taxon_data == 0
    taxon_data[zero_mask] = pseudocount
    zero_count = zero_mask.sum().sum()
    logger.info(f"Replaced {zero_count} zero values with pseudocount {pseudocount}.")
    
    # Step 2: Calculate geometric mean for each row
    # Geometric mean = exp(mean(log(x)))
    # We use np.log which is natural log.
    log_data = np.log(taxon_data)
    geometric_mean_log = log_data.mean(axis=1)
    
    # Step 3: CLR = log(x) - mean(log(x))
    clr_data = log_data.sub(geometric_mean_log, axis=0)
    
    # Rename columns to indicate CLR transformation
    clr_columns = [f"clr_{col}" for col in taxon_columns]
    clr_df = pd.DataFrame(clr_data, columns=clr_columns, index=df.index)
    
    # Concatenate back to original dataframe
    df = pd.concat([df, clr_df], axis=1)
    
    logger.info(f"CLR transformation complete. Added {len(clr_columns)} columns.")
    return df

def run_clr_transformation(input_path: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """
    Run the CLR transformation pipeline.
    Reads input, applies CLR, and saves output.
    """
    if input_path is None:
        input_path = str(get_processed_path() / "cleared_with_diversity.csv")
    if output_path is None:
        output_path = str(get_processed_path() / "cleared_with_diversity.csv")
    
    df, taxon_columns = load_filtered_data(input_path)
    df = apply_clr_transformation(df, taxon_columns)
    
    df.to_csv(output_path, index=False)
    logger.info(f"CLR transformed data saved to {output_path}")
    return output_path

def calculate_shannon_diversity(df: pd.DataFrame, taxon_columns: List[str]) -> pd.DataFrame:
    """
    Calculate Shannon diversity index for each subject.
    Shannon = -sum(p_i * log(p_i))
    """
    logger.info("Calculating Shannon diversity index...")
    
    # Ensure data is normalized (relative abundance)
    # Assuming input df has already been normalized in previous steps
    # If not, we could normalize here, but per task dependencies, it should be done.
    
    # Filter out zeros to avoid log(0)
    # We add a tiny epsilon if needed, but typically normalized data with zeros
    # should be handled by ignoring zero terms in the sum.
    
    shannon_values = []
    for _, row in df.iterrows():
        p = row[taxon_columns].values
        # Filter non-zero probabilities
        p_nonzero = p[p > 0]
        if len(p_nonzero) == 0:
            shannon_values.append(0.0)
        else:
            shannon = -np.sum(p_nonzero * np.log(p_nonzero))
            shannon_values.append(shannon)
    
    df['shannon_diversity'] = shannon_values
    logger.info("Shannon diversity calculation complete.")
    return df

def log_titer_statistics(df: pd.DataFrame) -> None:
    """
    Log basic statistics for titer columns.
    """
    logger.info("Logging titer statistics...")
    if 'titer_baseline' in df.columns:
        logger.info(f"Baseline titer stats:\n{df['titer_baseline'].describe()}")
    if 'titer_post' in df.columns:
        logger.info(f"Post titer stats:\n{df['titer_post'].describe()}")
    if 'log_titer' in df.columns:
        logger.info(f"Log titer stats:\n{df['log_titer'].describe()}")

def run_titer_log_transformation(input_path: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """
    Apply log transformation to titer_post and handle LOD if necessary.
    """
    if input_path is None:
        input_path = str(get_processed_path() / "cleared_with_diversity.csv")
    if output_path is None:
        output_path = str(get_processed_path() / "cleared_with_diversity.csv")
    
    df, _ = load_filtered_data(input_path)
    
    # LOD handling logic (simplified for this task, assuming LOD is handled or 1e-6 if 0)
    # If titer_post is 0, replace with a small value before log
    if 'titer_post' in df.columns:
        df['titer_post'] = df['titer_post'].replace(0, np.nan)
        # Impute missing/zero with a small value (e.g., 1e-6) or half LOD if known
        # For now, using a small constant as placeholder for LOD handling
        df['titer_post'] = df['titer_post'].fillna(1e-6)
        
        df['log_titer'] = np.log10(df['titer_post'])
        log_titer_statistics(df)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Log titer transformation complete. Saved to {output_path}")
    return output_path

def main():
    """
    Main entry point for the preprocessing script.
    Orchestrates the pipeline steps.
    """
    logger.info("Starting preprocessing pipeline...")
    
    # 1. Load data
    input_file = str(get_processed_path() / "cleared_with_diversity.csv")
    df, taxon_columns = load_filtered_data(input_file)
    
    # 2. Apply Normalization (Relative Abundance)
    df = apply_normalization(df, taxon_columns)
    
    # 3. Calculate Shannon Diversity (before CLR, as it depends on relative abundances)
    df = calculate_shannon_diversity(df, taxon_columns)
    
    # 4. Apply CLR Transformation
    df = apply_clr_transformation(df, taxon_columns)
    
    # 5. Log titer statistics (assuming log_titer might be added later or already present)
    # If log_titer is not present, this step might be skipped or handled by run_titer_log_transformation
    log_titer_statistics(df)
    
    # Save final output
    output_file = str(get_processed_path() / "cleared_with_diversity.csv")
    df.to_csv(output_file, index=False)
    
    logger.info(f"Preprocessing pipeline complete. Output saved to {output_file}")
    return output_file

if __name__ == "__main__":
    main()
