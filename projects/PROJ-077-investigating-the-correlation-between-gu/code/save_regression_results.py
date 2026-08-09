"""
Save regression summary results to CSV.

This module implements T027: Save regression summary (coefficient, std_err, p-value)
to data/processed/regression_results.csv.

It expects the regression results to be available in memory (typically returned
from the analysis pipeline) or loaded from a temporary source if the pipeline
was split. For this implementation, it assumes the regression model results
are passed in or retrieved from the analysis module's state.

To run standalone (for testing):
    python code/save_regression_results.py

This will attempt to run the analysis pipeline first to generate the data,
then save the results.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories, INPUT_PATHS, SAMPLE_LIMIT
from logging_config import get_logger, log_provenance, log_warning, log_pipeline_start, log_pipeline_end
from analysis import run_analysis_pipeline, load_processed_data

logger = get_logger(__name__)

# Output path for regression results
REGRESSION_RESULTS_PATH = Path("data/processed/regression_results.csv")

def load_regression_results_from_analysis() -> pd.DataFrame:
    """
    Run the analysis pipeline to get regression results and return them as a DataFrame.

    This function orchestrates the loading of data and running the regression
    analysis to produce the results needed for T027.

    Returns:
        pd.DataFrame: DataFrame containing regression results with columns:
            - predictor: Name of the predictor variable
            - coefficient: Estimated regression coefficient
            - std_err: Standard error of the coefficient
            - p_value: P-value for the coefficient
            - conf_int_lower: Lower bound of 95% confidence interval
            - conf_int_upper: Upper bound of 95% confidence interval
    """
    logger.info("Loading processed data for regression analysis...")
    df = load_processed_data()

    if df is None or df.empty:
        raise ValueError("Processed data is empty or not found. Cannot run regression.")

    logger.info(f"Loaded {len(df)} records for regression analysis.")

    # Run the full analysis pipeline which includes regression
    logger.info("Running analysis pipeline to generate regression results...")
    analysis_results = run_analysis_pipeline(df)

    if 'regression_results' not in analysis_results:
        raise KeyError("Regression results not found in analysis output. "
                       "Ensure T023 (multivariate regression) was executed successfully.")

    return analysis_results['regression_results']

def save_regression_results(results_df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save regression results to CSV file.

    Args:
        results_df: DataFrame containing regression results
        output_path: Optional custom output path. Defaults to REGRESSION_RESULTS_PATH.

    Returns:
        Path: The path where results were saved

    Raises:
        ValueError: If results_df is empty or missing required columns
    """
    if output_path is None:
        output_path = REGRESSION_RESULTS_PATH

    # Ensure output directory exists
    ensure_directories()

    # Validate required columns
    required_cols = ['coefficient', 'std_err', 'p_value']
    missing_cols = [col for col in required_cols if col not in results_df.columns]
    if missing_cols:
        raise ValueError(f"Regression results missing required columns: {missing_cols}")

    # Ensure 'predictor' column exists for clarity
    if 'predictor' not in results_df.columns:
        # If predictor names are in index, reset index and name the column
        if results_df.index.name is None:
            results_df = results_df.reset_index()
            results_df.columns = ['predictor'] + list(results_df.columns[1:])
        else:
            results_df = results_df.reset_index()

    # Save to CSV
    results_df.to_csv(output_path, index=False)
    logger.info(f"Saved regression results to {output_path}")
    log_provenance(f"Regression results saved: {output_path}", 
                  {"rows": len(results_df), "columns": list(results_df.columns)})

    return output_path

def run_save_regression_pipeline() -> Path:
    """
    Main entry point for the regression results saving pipeline.

    This function:
    1. Loads processed data
    2. Runs the analysis pipeline to generate regression results
    3. Saves the results to CSV

    Returns:
        Path: Path to the saved CSV file
    """
    log_pipeline_start("save_regression_results")

    try:
        # Get regression results from analysis
        results_df = load_regression_results_from_analysis()

        # Save to CSV
        output_path = save_regression_results(results_df)

        log_pipeline_end("save_regression_results", status="success")
        return output_path

    except Exception as e:
        log_warning(f"Failed to save regression results: {str(e)}")
        log_pipeline_end("save_regression_results", status="failed", error=str(e))
        raise

def main():
    """
    Command-line entry point.
    """
    print("Starting regression results saving pipeline...")
    try:
        output_path = run_save_regression_pipeline()
        print(f"Success! Regression results saved to: {output_path}")
        
        # Display summary
        df = pd.read_csv(output_path)
        print(f"\nRegression Results Summary:")
        print(f"  Total predictors: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"\nFirst few rows:")
        print(df.head())
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
