import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, Optional, List

from config import INPUT_PATHS, SAMPLE_LIMIT, RANDOM_SEED
from logging_config import get_logger, log_provenance, log_warning, log_pipeline_start, log_pipeline_end

logger = get_logger(__name__)

def calculate_shannon_index(df: pd.DataFrame, taxa_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Calculates the Shannon Index (alpha diversity) from raw OTU/ASV count data.
    
    CRITICAL: This function verifies that the input data consists of raw integer counts.
    It explicitly checks for float columns which would indicate CLR-transformed data
    and raises a ValueError if detected, ensuring compliance with FR-002 and SC-001.
    
    Args:
        df: DataFrame containing participant data and taxa columns.
        taxa_columns: List of column names representing taxa. If None, attempts to infer
                      based on column names or uses all non-metric columns.
    
    Returns:
        DataFrame with an added 'shannon_index' column.
    
    Raises:
        ValueError: If any taxa column contains float values (indicating transformed data)
                    or if non-integer values are detected in count columns.
    """
    if taxa_columns is None:
        # Heuristic: assume columns not in standard metadata are taxa
        metadata_cols = {'participant_id', 'age', 'sex', 'bmi', 'fluid_intelligence', 'dqs'}
        taxa_columns = [col for col in df.columns if col not in metadata_cols]
        if not taxa_columns:
            raise ValueError("Could not infer taxa columns. Please provide 'taxa_columns' argument.")
    
    logger.info(f"Calculating Shannon Index using {len(taxa_columns)} taxa columns")
    log_provenance("diversity", "calculate_shannon_index", f"Input columns: {taxa_columns}")

    # --- T020b: Verify Input Integrity ---
    # Check column types to ensure we have raw counts (integers), not CLR-transformed floats.
    # CLR transformation results in float64 data. Raw counts should be int64 or int32.
    for col in taxa_columns:
        if col not in df.columns:
            raise ValueError(f"Taxa column '{col}' not found in input DataFrame.")
        
        dtype = df[col].dtype
        
        # Check if the column is float (likely transformed)
        if np.issubdtype(dtype, np.floating):
            # Double check: are there actually non-integer values?
            # Sometimes raw data is loaded as float if there are NaNs, but we assume
            # the task implies CLR-transformed data which is distinctly float.
            # The prompt specifically says: "If any taxa column is float, raise ValueError"
            raise ValueError(
                f"Input data must be raw counts (integers), not transformed values. "
                f"Column '{col}' has dtype '{dtype}'. "
                f"Ensure you are passing raw OTU/ASV tables, not CLR-transformed data."
            )
        
        # Additional check: if it's integer but has non-integer values (e.g. loaded as float with decimals)
        # The prompt logic focuses on "float" dtype as the indicator of CLR.
        # However, robust code should ensure values are effectively integers.
        if not np.issubdtype(dtype, np.integer):
             # If it's not float (caught above) and not integer, it might be object or complex.
             # Let's try to coerce to int if possible, otherwise fail.
             try:
                 # Check if values are effectively integers (e.g. 1.0, 2.0)
                 if not np.all(df[col] == df[col].astype(int)):
                      raise ValueError(
                          f"Input data must be raw counts (integers). "
                          f"Column '{col}' contains non-integer values."
                      )
             except (ValueError, TypeError):
                  raise ValueError(
                      f"Input data must be raw counts (integers). "
                      f"Column '{col}' cannot be converted to integers."
                  )

    # Prepare counts matrix (ensure integers)
    counts_matrix = df[taxa_columns].astype(int)

    # Calculate Shannon Index using scikit-bio
    try:
        import skbio
        # scikit-bio expects 2D array-like
        shannon_values = skbio.diversity.alpha.shannon(counts_matrix.values)
    except ImportError:
        logger.error("scikit-bio is required for Shannon Index calculation. Install with: pip install scikit-bio")
        raise
    except Exception as e:
        logger.error(f"Error calculating Shannon Index: {e}")
        raise

    # Add result to DataFrame
    df_result = df.copy()
    df_result['shannon_index'] = shannon_values

    # Verify output
    if df_result['shannon_index'].isnull().any():
        log_warning("Some Shannon Index values are NaN (likely due to zero counts in all taxa).")
    
    log_provenance("diversity", "calculate_shannon_index", "Output: shannon_index column added")
    return df_result

def run_diversity_pipeline(input_path: str, output_path: str) -> None:
    """
    Orchestrates the diversity analysis pipeline:
    1. Loads raw taxa data.
    2. Verifies input integrity (T020b).
    3. Calculates Shannon Index.
    4. Saves results.
    """
    log_pipeline_start("diversity_pipeline")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info("Calculating Shannon Index...")
    df_with_shannon = calculate_shannon_index(df)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving results to {output_path}")
    df_with_shannon.to_csv(output_path, index=False)
    
    log_pipeline_end("diversity_pipeline", "Success")

def main():
    """Entry point for diversity pipeline."""
    # Default paths can be overridden by CLI args in a full implementation
    input_path = "data/raw/taxa_matrix.csv" 
    output_path = "data/processed/shannon_index.csv"
    
    # Check if raw data exists, if not, check for merged cleaned data which might have taxa
    # For this specific task, we assume the input is the taxa matrix or a merged file with taxa cols.
    # If the standard cleaned_data has taxa, we might adjust, but T020 is specifically about the calculation.
    # We will attempt to load from a standard location or the one provided in config if extended.
    # Given the current config, we look for the taxa matrix.
    
    if not os.path.exists(input_path):
        # Fallback: check if we need to join with cleaned data? 
        # The task T020 implies the input is the taxa table.
        # Let's assume the pipeline receives the correct path.
        # For now, if the default is missing, we try to find it or error.
        logger.warning(f"Default input {input_path} not found. Attempting to use cleaned data if it contains taxa.")
        if os.path.exists("data/processed/cleaned_data.csv"):
            input_path = "data/processed/cleaned_data.csv"
            output_path = "data/processed/shannon_index.csv"
        else:
            raise FileNotFoundError(f"Neither {input_path} nor data/processed/cleaned_data.csv found.")

    run_diversity_pipeline(input_path, output_path)

if __name__ == "__main__":
    main()