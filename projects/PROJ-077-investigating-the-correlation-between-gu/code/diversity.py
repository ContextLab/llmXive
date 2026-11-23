import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, Optional, List
import scikit_bio
from skbio.diversity import alpha_diversity
from config import INPUT_PATHS, RANDOM_SEED, SAMPLE_LIMIT
from logging_config import get_logger, log_operation, log_pipeline_start, log_pipeline_end, log_provenance, log_warning

logger = get_logger("diversity")

def calculate_shannon_index(counts_matrix):
    """
    Calculate Shannon Index (alpha diversity) from raw counts.
    
    Args:
        counts_matrix: DataFrame or 2D array of OTU counts (rows=participants, cols=taxa).
        
    Returns:
        pd.Series: Shannon diversity indices.
    """
    # Validate input
    if not isinstance(counts_matrix, (pd.DataFrame, np.ndarray)):
        raise ValueError("Input must be a DataFrame or numpy array.")
        
    if not np.issubdtype(counts_matrix.dtype, np.number):
        raise ValueError("Input matrix must contain numeric values.")
        
    # Ensure non-negative
    if (counts_matrix < 0).any().any():
        raise ValueError("Count matrix must contain non-negative values.")
        
    # Calculate Shannon index
    try:
        shannon = alpha_diversity('shannon', counts_matrix)
        return shannon
    except Exception as e:
        log_warning(f"Shannon calculation failed: {e}")
        raise

def validate_input_integrity(df):
    """
    Validate that the input DataFrame has the expected structure.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    if df.empty:
        log_warning("Input DataFrame is empty.")
        return False
        
    # Check for at least one numeric column
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        log_warning("No numeric columns found in input DataFrame.")
        return False
        
    return True

def run_diversity_pipeline():
    """
    Run the diversity analysis pipeline.
    Loads raw microbiome data, calculates Shannon index, and appends to cleaned data.
    """
    log_pipeline_start("Diversity Pipeline")
    
    try:
        # Load raw microbiome data (excluding ID columns)
        microbiome_path = INPUT_PATHS["microbiome"]
        if not os.path.exists(microbiome_path):
            log_warning(f"Microbiome data not found at {microbiome_path}. Skipping diversity calculation.")
            return
            
        # Load with streaming if large
        df_raw = pd.read_csv(microbiome_path)
        
        # Identify ID column
        id_col = None
        for c in ['participant_id', 'eid', 'subject_id']:
            if c in df_raw.columns:
                id_col = c
                break
                
        if not id_col:
            log_warning("No ID column found in microbiome data.")
            return
            
        # Get taxa columns (all numeric except ID)
        taxa_cols = [c for c in df_raw.select_dtypes(include=[np.number]).columns if c != id_col]
        
        if not taxa_cols:
            log_warning("No taxa columns found.")
            return
            
        # Calculate Shannon index
        counts = df_raw[taxa_cols].values
        shannon_idx = calculate_shannon_index(counts)
        
        # Create a DataFrame with ID and Shannon
        shannon_df = pd.DataFrame({
            id_col: df_raw[id_col].values,
            'shannon_index': shannon_idx
        })
        
        # Load cleaned data
        cleaned_path = Path("data/processed/cleaned_data.csv")
        if cleaned_path.exists():
            df_cleaned = pd.read_csv(cleaned_path)
            id_col_cleaned = None
            for c in ['participant_id', 'eid', 'subject_id']:
                if c in df_cleaned.columns:
                    id_col_cleaned = c
                    break
                    
            if not id_col_cleaned:
                id_col_cleaned = id_col
                
            # Merge Shannon back
            df_cleaned = pd.merge(df_cleaned, shannon_df, left_on=id_col_cleaned, right_on=id_col, how='left')
            df_cleaned.to_csv(cleaned_path, index=False)
            log_provenance("Shannon index appended to cleaned data.")
        else:
            log_warning("Cleaned data not found. Saving Shannon index separately.")
            shannon_df.to_csv("data/processed/shannon_index.csv", index=False)
            
    except Exception as e:
        log_pipeline_end("Diversity Pipeline failed.", error=str(e))
        raise

def main():
    """Entry point for diversity analysis."""
    run_diversity_pipeline()

if __name__ == "__main__":
    main()
