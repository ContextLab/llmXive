"""
Module to save Spearman correlation results to a CSV file.
This task (T026) implements the saving of correlation results.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

# Import from sibling modules based on API surface
from config import ensure_directories
from logging_config import get_logger, log_provenance, log_warning

logger = get_logger(__name__)

def save_correlation_results(r_value: float, p_value: float, n_obs: int, output_path: str) -> None:
    """
    Saves the correlation results to a CSV file.

    Args:
        r_value: The Spearman correlation coefficient.
        p_value: The p-value of the correlation test.
        n_obs: The number of observations.
        output_path: The path where the CSV file will be saved.
    """
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Create a DataFrame with the results
    results_df = pd.DataFrame({
        'r_value': [r_value],
        'p_value': [p_value],
        'n_obs': [n_obs]
    })

    # Save to CSV
    results_df.to_csv(output_path, index=False)
    logger.info(f"Correlation results saved to {output_path}")
    log_provenance(f"Saved correlation results: r={r_value}, p={p_value}, n={n_obs}")

def run_save_correlation_pipeline(
    r_value: float,
    p_value: float,
    n_obs: int,
    output_path: Optional[str] = None
) -> None:
    """
    Runs the pipeline to save correlation results.

    Args:
        r_value: The Spearman correlation coefficient.
        p_value: The p-value of the correlation test.
        n_obs: The number of observations.
        output_path: Optional custom output path. Defaults to 'data/processed/correlation_results.csv'.
    """
    if output_path is None:
        output_path = "data/processed/correlation_results.csv"

    logger.info(f"Starting correlation results save pipeline to {output_path}")
    
    # Validate inputs
    if not isinstance(r_value, (int, float)):
        raise TypeError(f"r_value must be a number, got {type(r_value)}")
    if not isinstance(p_value, (int, float)):
        raise TypeError(f"p_value must be a number, got {type(p_value)}")
    if not isinstance(n_obs, int):
        raise TypeError(f"n_obs must be an integer, got {type(n_obs)}")
    
    if n_obs <= 0:
        raise ValueError(f"n_obs must be positive, got {n_obs}")

    save_correlation_results(r_value, p_value, n_obs, output_path)
    logger.info("Correlation results save pipeline completed successfully")

def main():
    """
    Main entry point for the script.
    This script is intended to be called by the analysis pipeline or main.py.
    It expects the correlation values to be passed or retrieved from a previous step.
    For direct execution, it will log a message indicating it needs parameters.
    """
    logger.info("save_correlation_results.py executed directly. Use as a module.")
    print("This module is designed to be imported and called with specific values.")
    print("Example: from save_correlation_results import run_save_correlation_pipeline")
    print("         run_save_correlation_pipeline(r=0.5, p=0.01, n=100)")

if __name__ == "__main__":
    main()