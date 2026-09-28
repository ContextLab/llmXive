"""
Module to save regression results to CSV.
Implements T027: Save regression summary with coefficient, std_err, p_value.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from config import ensure_directories, INPUT_PATHS, SAMPLE_LIMIT
from logging_config import get_logger, log_provenance, log_warning, log_pipeline_start, log_pipeline_end

logger = get_logger(__name__)

def load_regression_results_from_analysis() -> Optional[pd.DataFrame]:
    """
    Load regression results from the analysis module's output.
    Since T023 (run_multivariate_regression) writes to data/processed/regression_results.csv,
    we read that file here to validate and re-save if necessary, or return the DataFrame
    if T023 has already populated it in memory (though the spec says T023 writes to disk).
    
    For T027, we assume T023 has run and written the file. We load it, validate, and ensure
    it is saved correctly.
    
    Returns:
        DataFrame with columns: coefficient, std_err, p_value, or None if not found.
    """
    output_path = "data/processed/regression_results.csv"
    
    if not os.path.exists(output_path):
        logger.warning(f"Regression results file not found at {output_path}. "
                       "This may indicate T023 has not run yet.")
        return None
    
    try:
        df = pd.read_csv(output_path)
        logger.info(f"Loaded regression results from {output_path} with {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to load regression results: {e}")
        return None

def save_regression_results(df: pd.DataFrame, output_path: str = "data/processed/regression_results.csv") -> bool:
    """
    Save the regression results DataFrame to CSV with the exact required columns:
    coefficient, std_err, p_value.
    
    Args:
        df: DataFrame containing regression results.
        output_path: Path to save the CSV file.
        
    Returns:
        True if saved successfully, False otherwise.
    """
    try:
        # Ensure the output directory exists
        ensure_directories()
        
        # Validate that required columns exist
        required_cols = ['coefficient', 'std_err', 'p_value']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns in regression results: {missing_cols}")
        
        # Select only the required columns in the correct order
        result_df = df[required_cols].copy()
        
        # Save to CSV
        result_df.to_csv(output_path, index=False)
        logger.info(f"Saved regression results to {output_path} with {len(result_df)} rows.")
        log_provenance(f"Regression results saved to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save regression results: {e}")
        return False

def run_save_regression_pipeline() -> bool:
    """
    Run the pipeline to load and save regression results.
    
    Returns:
        True if the pipeline completed successfully, False otherwise.
    """
    log_pipeline_start("save_regression_results")
    
    # Load results from the analysis output
    df = load_regression_results_from_analysis()
    
    if df is None:
        log_warning("No regression results found to save. Ensure T023 (run_multivariate_regression) has run.")
        log_pipeline_end("save_regression_results", success=False)
        return False
    
    # Save the results
    success = save_regression_results(df)
    
    log_pipeline_end("save_regression_results", success=success)
    return success

def main():
    """
    Entry point for the save regression results script.
    """
    success = run_save_regression_pipeline()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()