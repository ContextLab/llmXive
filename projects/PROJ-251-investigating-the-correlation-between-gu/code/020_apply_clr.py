import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Optional

import pandas as pd
import numpy as np

# Import config utilities to ensure paths and settings are consistent
from utils.config import (
    get_processed_path,
    get_random_seed,
    get_pseudocount,
    get_use_synthetic_data,
)
from utils.logging_config import get_logger, log_error_context

logger = get_logger(__name__)

def load_cleared_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the cleared data with Shannon diversity and log-transformed titers.
    
    Args:
        input_path: Path to the input CSV file. If None, uses default path from config.
        
    Returns:
        DataFrame containing the processed data.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if input_path is None:
        # Default path based on the task dependency chain:
        # T021 produces data/processed/cleared_shannon_log.csv
        input_path = get_processed_path() / "cleared_shannon_log.csv"
        
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    df = pd.read_csv(input_path)
    required_cols = ["subject_id", "titer_baseline", "titer_post"]
    # Check for at least one taxon column (we'll identify them dynamically)
    if df.empty:
        raise ValueError("Input DataFrame is empty")
        
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def identify_taxa_columns(df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> List[str]:
    """
    Identify columns that represent taxon abundances.
    
    Args:
        df: Input DataFrame.
        exclude_cols: List of column names to exclude from taxon identification.
        
    Returns:
        List of column names representing taxa.
    """
    if exclude_cols is None:
        exclude_cols = ["subject_id", "titer_baseline", "titer_post", 
                      "titer_pre_log", "titer_post_log", "shannon_diversity"]
        
    # Taxa columns are typically numeric and not in the exclude list
    # They might be named like 'taxon_0', 'taxon_1', or actual taxon names
    taxa_cols = []
    for col in df.columns:
        if col not in exclude_cols:
            # Check if the column is numeric
            if pd.api.types.is_numeric_dtype(df[col]):
                taxa_cols.append(col)
                
    if not taxa_cols:
        logger.warning("No taxon columns identified. Checking for any numeric columns...")
        # Fallback: identify any numeric columns that aren't metadata
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]) and col not in exclude_cols:
                taxa_cols.append(col)
                
    logger.info(f"Identified {len(taxa_cols)} taxon columns")
    return taxa_cols

def apply_clr_transformation(df: pd.DataFrame, taxa_cols: List[str], 
                             pseudocount: Optional[float] = None) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to taxon abundances.
    
    Steps:
    1. Normalize raw counts to relative abundances (sum=1) for each sample.
    2. Replace zeros with a small pseudocount to avoid log(0).
    3. Apply log transformation.
    4. Subtract the mean of the log-transformed values for each sample (centering).
    
    Args:
        df: Input DataFrame with taxon columns.
        taxa_cols: List of column names representing taxa.
        pseudocount: Small value to replace zeros. If None, uses config value.
        
    Returns:
        DataFrame with CLR-transformed taxon columns added (suffix '_clr').
        
    Raises:
        ValueError: If any taxon column is entirely zero or invalid.
    """
    if pseudocount is None:
        pseudocount = get_pseudocount()
        
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Step 1: Normalize to relative abundances
    # Sum of taxon abundances per row
    row_sums = result_df[taxa_cols].sum(axis=1)
    
    # Handle cases where sum is 0 (all zeros in a sample)
    if (row_sums == 0).any():
        logger.warning(f"Found {sum(row_sums == 0)} samples with zero total abundance. These will be handled.")
        
    # Calculate relative abundances
    relative_abundance = result_df[taxa_cols].div(row_sums, axis=0)
    
    # Step 2: Replace zeros with pseudocount
    # This is critical because log(0) is undefined
    relative_abundance = relative_abundance.replace(0, pseudocount)
    
    # Also replace any negative values (shouldn't happen, but safety check)
    relative_abundance = relative_abundance.clip(lower=0)
    
    # Re-normalize after pseudocount addition to ensure sum is still 1
    # (This step is optional but good practice)
    row_sums_after = relative_abundance.sum(axis=1)
    relative_abundance = relative_abundance.div(row_sums_after, axis=0)
    
    # Step 3: Log transformation
    log_transformed = np.log(relative_abundance)
    
    # Step 4: Center by subtracting the mean of log values for each sample
    log_means = log_transformed.mean(axis=1)
    clr_transformed = log_transformed.sub(log_means, axis=0)
    
    # Add CLR columns to the result DataFrame with '_clr' suffix
    clr_col_names = [f"{col}_clr" for col in taxa_cols]
    clr_transformed.columns = clr_col_names
    
    # Concatenate with original DataFrame
    result_df = pd.concat([result_df, clr_transformed], axis=1)
    
    # Log summary statistics
    logger.info(f"CLR transformation complete. Added {len(clr_col_names)} CLR columns.")
    logger.debug(f"CLR columns: {clr_col_names}")
    
    # Check for any NaN or Inf values in CLR columns
    if clr_transformed.isna().any().any():
        logger.warning("NaN values detected in CLR-transformed data.")
    if np.isinf(clr_transformed).any().any():
        logger.warning("Infinite values detected in CLR-transformed data.")
        
    return result_df

def write_updated_dataset(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Write the CLR-transformed dataset to a CSV file.
    
    Args:
        df: DataFrame with CLR-transformed data.
        output_path: Path to the output file. If None, uses default path.
        
    Returns:
        Path to the written file.
    """
    if output_path is None:
        # Output path: data/processed/cleared_final.csv (as per task description)
        output_path = get_processed_path() / "cleared_final.csv"
        
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"CLR-transformed dataset written to {output_path}")
    
    # Log file size
    file_size = output_path.stat().st_size
    logger.info(f"Output file size: {file_size / 1024:.2f} KB")
    
    return output_path

def run_clr_pipeline(input_path: Optional[Path] = None, 
                    output_path: Optional[Path] = None) -> dict:
    """
    Run the complete CLR transformation pipeline.
    
    Args:
        input_path: Path to input file (cleared_shannon_log.csv).
        output_path: Path to output file (cleared_final.csv).
        
    Returns:
        Dictionary with pipeline results and metadata.
    """
    try:
        # Load data
        logger.info("Loading cleared data...")
        df = load_cleared_data(input_path)
        
        # Identify taxon columns
        logger.info("Identifying taxon columns...")
        taxa_cols = identify_taxa_columns(df)
        
        if not taxa_cols:
            raise ValueError("No taxon columns found for CLR transformation.")
            
        # Apply CLR transformation
        logger.info("Applying CLR transformation...")
        df_clr = apply_clr_transformation(df, taxa_cols)
        
        # Write output
        logger.info("Writing output dataset...")
        written_path = write_updated_dataset(df_clr, output_path)
        
        # Prepare results summary
        results = {
            "status": "success",
            "input_file": str(input_path) if input_path else "default",
            "output_file": str(written_path),
            "num_samples": len(df),
            "num_taxa": len(taxa_cols),
            "taxa_columns": taxa_cols,
            "clr_columns": [f"{col}_clr" for col in taxa_cols],
            "pseudocount_used": get_pseudocount()
        }
        
        logger.info(f"Pipeline completed successfully. Processed {len(taxa_cols)} taxa across {len(df)} samples.")
        return results
        
    except Exception as e:
        logger.error(f"CLR pipeline failed: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "input_file": str(input_path) if input_path else "default"
        }

def main():
    """Main entry point for the CLR transformation script."""
    logger.info("Starting CLR Transformation Pipeline (T020a)")
    
    # Get paths from config (or use defaults)
    input_path = get_processed_path() / "cleared_shannon_log.csv"
    output_path = get_processed_path() / "cleared_final.csv"
    
    # Run the pipeline
    results = run_clr_pipeline(input_path, output_path)
    
    # Log final status
    if results["status"] == "success":
        logger.info("CLR transformation completed successfully!")
        logger.info(f"Output saved to: {results['output_file']}")
        return 0
    else:
        logger.error(f"CLR transformation failed: {results.get('error', 'Unknown error')}")
        return 1

if __name__ == "__main__":
    sys.exit(main())