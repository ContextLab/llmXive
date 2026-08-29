import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import pandas as pd
import numpy as np

from utils.config import get_pseudocount, get_random_seed
from utils.logging_config import get_logger, log_exclusion_count, log_error_context

# Ensure the module can be imported from the project root
sys.path.insert(0, str(Path(__file__).parent))

logger = get_logger(__name__)

def load_filtered_data(input_path: Path) -> pd.DataFrame:
    """
    Load the merged and filtered dataset from data/processed/data_norm.csv.
    This file is expected to contain normalized taxa abundances.
    """
    logger.info(f"Loading filtered data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Identify taxon columns (all columns except subject_id and metadata)
    exclude_cols = {'subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity'}
    taxon_cols = [col for col in df.columns if col not in exclude_cols]
    
    if len(taxon_cols) == 0:
        logger.warning("No taxon columns found in the dataset.")
    
    logger.info(f"Loaded {len(df)} subjects with {len(taxon_cols)} taxa.")
    return df

def calculate_shannon_diversity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the Shannon diversity index for each subject based on normalized taxa abundances.
    
    Formula: H = - sum(p_i * ln(p_i)) for all taxa i where p_i > 0
    
    Args:
        df: DataFrame containing normalized taxon abundances.
        
    Returns:
        DataFrame with an added 'shannon_diversity' column.
    """
    logger.info("Calculating Shannon diversity index.")
    
    # Identify taxon columns (non-metadata columns)
    exclude_cols = {'subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity'}
    taxon_cols = [col for col in df.columns if col not in exclude_cols]
    
    if len(taxon_cols) == 0:
        logger.warning("No taxon columns found for Shannon diversity calculation.")
        df['shannon_diversity'] = 0.0
        return df

    # Create a copy to avoid modifying the original
    df_shannon = df.copy()
    
    # Calculate Shannon index row-wise
    # H = - sum(p * ln(p))
    # We only sum where p > 0 to avoid log(0)
    
    def shannon_calc(row):
        # Filter out zeros and metadata
        abundances = row[taxon_cols].values
        # Filter positive abundances
        p = abundances[abundances > 0]
        if len(p) == 0:
            return 0.0
        return -np.sum(p * np.log(p))
    
    df_shannon['shannon_diversity'] = df_shannon.apply(shannon_calc, axis=1)
    
    # Log statistics
    mean_shannon = df_shannon['shannon_diversity'].mean()
    std_shannon = df_shannon['shannon_diversity'].std()
    logger.info(f"Shannon diversity calculated. Mean: {mean_shannon:.4f}, Std: {std_shannon:.4f}")
    
    return df_shannon

def run_shannon_pipeline(input_path: Path, output_path: Path) -> Path:
    """
    Run the Shannon diversity calculation pipeline.
    
    Args:
        input_path: Path to the input CSV (data_norm.csv).
        output_path: Path to write the output CSV (data_div.csv).
        
    Returns:
        Path to the output file.
    """
    logger.info(f"Starting Shannon diversity pipeline: {input_path} -> {output_path}")
    
    # Load data
    df = load_filtered_data(input_path)
    
    # Calculate Shannon diversity
    df_shannon = calculate_shannon_diversity(df)
    
    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_shannon.to_csv(output_path, index=False)
    
    logger.info(f"Shannon diversity pipeline complete. Output written to {output_path}")
    return output_path

def apply_clr_transformation(df: pd.DataFrame, pseudocount: float = 1e-6) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to taxon abundance columns.
    
    Steps:
    1. Zero-replacement: Add a small pseudocount to all zero abundances.
    2. Log-transform: Take the natural logarithm of the abundances.
    3. Centering: Subtract the geometric mean (mean of log-transformed values) for each sample.
    
    Args:
        df: DataFrame containing normalized taxon abundances.
        pseudocount: Small value to add to zeros to avoid log(0).
        
    Returns:
        DataFrame with CLR-transformed columns (suffix '_clr').
    """
    logger.info(f"Applying CLR transformation with pseudocount={pseudocount}")
    
    # Identify taxon columns (non-metadata columns)
    exclude_cols = {'subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity'}
    taxon_cols = [col for col in df.columns if col not in exclude_cols]
    
    if len(taxon_cols) == 0:
        logger.warning("No taxon columns found for CLR transformation.")
        return df

    # Create a copy to avoid modifying the original
    df_clr = df.copy()
    
    # Step 1: Zero-replacement
    # Check for zeros
    zero_counts = (df_clr[taxon_cols] == 0).sum()
    total_zeros = zero_counts.sum()
    if total_zeros > 0:
        logger.info(f"Found {total_zeros} zero values in taxon abundances. Replacing with pseudocount.")
        # Add pseudocount to all values (safe for non-zeros too, as it's very small)
        df_clr[taxon_cols] = df_clr[taxon_cols] + pseudocount
    else:
        logger.info("No zero values found in taxon abundances. Proceeding without replacement.")
    
    # Step 2: Log-transform
    df_clr[taxon_cols] = np.log(df_clr[taxon_cols])
    
    # Step 3: Centering (subtract row-wise mean of log values)
    # The geometric mean of x is exp(mean(log(x))), so log(geometric_mean) = mean(log(x))
    # CLR(x_i) = log(x_i) - mean(log(x_j) for all j)
    log_means = df_clr[taxon_cols].mean(axis=1)
    for col in taxon_cols:
        df_clr[col] = df_clr[col] - log_means
        # Rename to indicate CLR transformation
        new_col_name = f"{col}_clr"
        df_clr[new_col_name] = df_clr[col]
    
    # Drop the original log-transformed columns to keep the dataframe clean
    # Keep only the CLR versions
    cols_to_drop = taxon_cols
    df_clr = df_clr.drop(columns=cols_to_drop)
    
    logger.info(f"CLR transformation complete. Generated {len(taxon_cols)} CLR columns.")
    return df_clr

def run_clr_pipeline(input_path: Path, output_path: Path, pseudocount: Optional[float] = None) -> Path:
    """
    Run the CLR transformation pipeline.
    
    Args:
        input_path: Path to the input CSV (data_log.csv).
        output_path: Path to write the output CSV (data_clr.csv).
        pseudocount: Optional custom pseudocount. Uses config default if None.
        
    Returns:
        Path to the output file.
    """
    logger.info(f"Starting CLR pipeline: {input_path} -> {output_path}")
    
    # Load data
    df = load_filtered_data(input_path)
    
    # Get pseudocount
    if pseudocount is None:
        pseudocount = get_pseudocount()
    
    # Apply CLR
    df_clr = apply_clr_transformation(df, pseudocount=pseudocount)
    
    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_clr.to_csv(output_path, index=False)
    
    logger.info(f"CLR pipeline complete. Output written to {output_path}")
    return output_path

def main():
    """Main entry point for the preprocessing tasks (Shannon Diversity and CLR)."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    
    # Paths for Shannon Diversity (T020c)
    input_norm_path = project_root / "data" / "processed" / "data_norm.csv"
    output_div_path = project_root / "data" / "processed" / "data_div.csv"
    
    # Paths for CLR (T020a) - depends on data_log.csv which is produced after log transform (T021)
    # Note: T021 produces data_log.csv. T020c produces data_div.csv.
    # The task T020c specifically asks for Shannon on data_norm.csv.
    # The task T020a (CLR) expects data_log.csv as input according to the task description.
    # However, the existing code structure in 02_preprocess.py seems to expect data_log.csv for CLR.
    # We will run Shannon first as requested by T020c.
    
    try:
        # Execute T020c: Calculate Shannon Diversity
        logger.info("Executing Task T020c: Calculate Shannon Diversity Index")
        run_shannon_pipeline(input_norm_path, output_div_path)
        logger.info("Task T020c (Shannon Diversity) completed successfully.")
        
        # Note: T020a (CLR) is also implemented in this file but requires data_log.csv as input.
        # The main execution for CLR would be triggered separately or as part of a larger pipeline.
        # For this specific task T020c, we ensure Shannon is calculated.
        
    except Exception as e:
        log_error_context(logger, "Task T020c failed", e)
        sys.exit(1)

if __name__ == "__main__":
    main()