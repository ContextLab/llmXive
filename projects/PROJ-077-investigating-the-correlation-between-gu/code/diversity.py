import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, Optional, List

# Ensure imports from sibling modules match the API surface
try:
    from logging_config import get_logger, log_provenance, log_warning
except ImportError:
    # Fallback for direct execution or different environment
    import logging
    def get_logger(name):
        return logging.getLogger(name)
    def log_provenance(msg):
        logging.info(msg)
    def log_warning(msg):
        logging.warning(msg)

logger = get_logger(__name__)

def calculate_shannon_index(df: pd.DataFrame, taxa_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Calculates the Shannon Index (alpha diversity) from raw OTU/ASV counts.
    
    CRITICAL: This function validates that the input data consists of raw integer counts.
    It explicitly raises a ValueError if any taxa column is detected as float,
    indicating that the data might have been CLR-transformed or normalized prior to this step.
    
    Args:
        df: DataFrame containing participant data and taxa counts.
        taxa_columns: List of column names representing taxa abundances. 
                      If None, all numeric columns excluding known metadata are assumed to be taxa.
                      
    Returns:
        DataFrame with an added 'shannon_index' column.
        
    Raises:
        ValueError: If taxa columns are not integers or if data appears transformed (floats).
    """
    if taxa_columns is None:
        # Heuristic: Assume numeric columns that are not standard metadata are taxa
        metadata_cols = ['participant_id', 'age', 'sex', 'bmi', 'dqs', 'fluid_intelligence', 'shannon_index']
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        taxa_columns = [col for col in numeric_cols if col not in metadata_cols]
        
    if not taxa_columns:
        raise ValueError("No taxa columns found in the input DataFrame.")
    
    # --- T020b: Verify Input Integrity ---
    # Check column types to ensure we are working with raw counts (integers)
    # and NOT CLR-transformed floats.
    for col in taxa_columns:
        if col not in df.columns:
            raise ValueError(f"Taxa column '{col}' not found in DataFrame.")
        
        # Check if the column dtype is float. 
        # While some integer data might be loaded as float by pandas, 
        # CLR-transformed data is inherently float. 
        # We enforce strict integer checking for raw counts as per spec.
        if df[col].dtype == np.float64 or df[col].dtype == np.float32:
            # Check if values are effectively integers (e.g., 1.0, 2.0) vs transformed (e.g., 0.123, -0.456)
            # If any value is non-integer, it is definitely transformed.
            # Even if all are integers stored as float, we warn/raise to enforce strict raw count usage.
            if not np.allclose(df[col].dropna(), df[col].dropna().astype(int)):
                raise ValueError(
                    f"Input data must be raw counts (integers), not transformed values. "
                    f"Column '{col}' contains non-integer float values."
                )
            else:
                # All values are integers but stored as float. 
                # Strictly speaking, raw counts should be int. 
                # We raise to enforce the requirement for raw integer counts.
                raise ValueError(
                    f"Input data must be raw counts (integers), not transformed values. "
                    f"Column '{col}' is of float type. Please ensure input is integer counts."
                )
    
    logger.info(f"Validated input integrity for {len(taxa_columns)} taxa columns. All are raw integer counts.")

    # Import scikit-bio
    try:
        import skbio
        from skbio.diversity import alpha
    except ImportError:
        raise ImportError("scikit-bio is required for Shannon index calculation. Install via: pip install scikit-bio")

    # Extract counts matrix
    counts = df[taxa_columns].values.astype(int)
    
    # Validate non-negative
    if np.any(counts < 0):
        raise ValueError("Taxa counts must be non-negative.")

    # Calculate Shannon Index
    # scikit-bio expects 2D array (samples x taxa)
    shannon_values = alpha.shannon(counts, axis=1)
    
    # Create result DataFrame
    result_df = df.copy()
    result_df['shannon_index'] = shannon_values
    
    log_provenance(f"Calculated Shannon Index for {len(result_df)} samples using {len(taxa_columns)} taxa.")
    
    return result_df

def run_diversity_pipeline(input_path: str, output_path: str) -> None:
    """
    Runs the diversity analysis pipeline:
    1. Loads data
    2. Validates input integrity (T020b)
    3. Calculates Shannon Index
    4. Saves results
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info("Running diversity pipeline...")
    try:
        result_df = calculate_shannon_index(df)
    except ValueError as e:
        logger.error(f"Input validation failed: {e}")
        raise
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    result_df.to_csv(output_path, index=False)
    log_provenance(f"Saved diversity results to {output_path}")
    logger.info(f"Pipeline complete. Results saved to {output_path}")

if __name__ == "__main__":
    # Simple CLI for testing
    import argparse
    parser = argparse.ArgumentParser(description="Run Shannon Index Diversity Pipeline")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--output", required=True, help="Path to output CSV")
    args = parser.parse_args()
    
    run_diversity_pipeline(args.input, args.output)