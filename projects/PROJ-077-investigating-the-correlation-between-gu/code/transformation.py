import numpy as np
import pandas as pd
from typing import Union
import logging
from pathlib import Path
import os
from config import INPUT_PATHS
from logging_config import get_logger, log_operation, log_pipeline_start, log_pipeline_end, log_provenance, log_warning

logger = get_logger("transformation")

def apply_clr(counts_matrix):
    """
    Apply Centered Log-Ratio (CLR) transformation to taxa abundance matrix.
    
    Args:
        counts_matrix: DataFrame or 2D array of taxa abundances.
        
    Returns:
        np.ndarray: CLR-transformed matrix.
    """
    if not isinstance(counts_matrix, np.ndarray):
        counts_matrix = counts_matrix.values
        
    # Add pseudocount to avoid log(0)
    counts_matrix = np.where(counts_matrix == 0, 1e-6, counts_matrix)
    
    # Calculate geometric mean for each row
    log_counts = np.log(counts_matrix)
    geom_mean = np.exp(np.mean(log_counts, axis=1, keepdims=True))
    
    # CLR: log(x_i / g(x))
    clr_result = log_counts - np.log(geom_mean)
    
    return clr_result

def validate_clr_property(df):
    """
    Validate that the input DataFrame is suitable for CLR.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        bool: True if valid.
    """
    if df.empty:
        return False
    
    # Check for positive values only (or zero with pseudocount)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        return False
        
    return True

def run_transformation_pipeline():
    """
    Run the CLR transformation pipeline.
    Loads cleaned data, applies CLR to taxa, and saves results.
    """
    log_pipeline_start("Transformation Pipeline")
    
    try:
        # Load cleaned data
        cleaned_path = Path("data/processed/cleaned_data.csv")
        if not cleaned_path.exists():
            log_warning("Cleaned data not found. Skipping transformation.")
            return
            
        df = pd.read_csv(cleaned_path)
        
        # Identify taxa columns (numeric, excluding known non-taxa)
        exclude = ['participant_id', 'age', 'bmi', 'sex', 'shannon_index', 'fluid_intelligence_score', 'dietary_quality_score']
        taxa_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude]
        
        if not taxa_cols:
            log_warning("No taxa columns found for transformation.")
            return
            
        # Apply CLR
        taxa_matrix = df[taxa_cols]
        clr_matrix = apply_clr(taxa_matrix)
        
        # Save CLR results
        clr_df = pd.DataFrame(clr_matrix, columns=taxa_cols)
        clr_df['participant_id'] = df['participant_id'].values
        clr_path = Path("data/processed/clr_taxa.csv")
        clr_df.to_csv(clr_path, index=False)
        log_provenance(f"CLR transformed data saved to {clr_path}")
        
    except Exception as e:
        log_pipeline_end("Transformation Pipeline failed.", error=str(e))
        raise

def main():
    """Entry point for transformation."""
    run_transformation_pipeline()

if __name__ == "__main__":
    main()
