"""
Module for saving analysis results to CSV files.
Implements T030: Save permutation results and sensitivity summary.
"""
import os
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from config import get_config

logger = logging.getLogger(__name__)

def save_permutation_results(
    p_values: List[float],
    distribution_of_max_stats: List[float],
    output_path: Optional[str] = None
) -> Path:
    """
    Save permutation test results to a CSV file.

    Args:
        p_values: List of empirical p-values from permutation tests.
        distribution_of_max_stats: List of max statistics from permutation distribution.
        output_path: Path to save the CSV file. Defaults to config.INTERIM_PATH / 'permutation_results.csv'.

    Returns:
        Path to the saved file.

    Raises:
        ValueError: If input lists are empty or of different lengths.
    """
    config = get_config()
    if output_path is None:
        output_path = str(config.DATA_PATH / "interim" / "permutation_results.csv")

    if not p_values or not distribution_of_max_stats:
        raise ValueError("p_values and distribution_of_max_stats lists cannot be empty")
    
    if len(p_values) != len(distribution_of_max_stats):
        raise ValueError("p_values and distribution_of_max_stats must have the same length")

    df = pd.DataFrame({
        'p_value': p_values,
        'max_stat': distribution_of_max_stats
    })

    # Ensure directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)
    logger.info(f"Saved permutation results to {output_path}")
    return output_file

def save_sensitivity_summary(
    sensitivity_df: pd.DataFrame,
    output_path: Optional[str] = None
) -> Path:
    """
    Save sensitivity analysis summary to a CSV file.

    Args:
        sensitivity_df: DataFrame containing sensitivity analysis results
                       (must have columns: window_length, correlation, p_value).
        output_path: Path to save the CSV file. Defaults to config.INTERIM_PATH / 'sensitivity_summary.csv'.

    Returns:
        Path to the saved file.

    Raises:
        ValueError: If DataFrame is missing required columns.
    """
    config = get_config()
    if output_path is None:
        output_path = str(config.DATA_PATH / "interim" / "sensitivity_summary.csv")

    required_columns = {'window_length', 'correlation', 'p_value'}
    if not required_columns.issubset(sensitivity_df.columns):
        missing = required_columns - set(sensitivity_df.columns)
        raise ValueError(f"Sensitivity DataFrame missing required columns: {missing}")

    # Ensure directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    sensitivity_df.to_csv(output_path, index=False)
    logger.info(f"Saved sensitivity summary to {output_path}")
    return output_file

def save_fwe_corrected_results(
    adjusted_p_values: List[float],
    original_p_values: List[float],
    method: str,
    output_path: Optional[str] = None
) -> Path:
    """
    Save FWE-corrected p-values alongside original values.

    Args:
        adjusted_p_values: List of FWE-corrected p-values.
        original_p_values: List of original p-values.
        method: The correction method used (e.g., 'max-t', 'bonferroni').
        output_path: Path to save the CSV file.

    Returns:
        Path to the saved file.
    """
    config = get_config()
    if output_path is None:
        output_path = str(config.DATA_PATH / "interim" / "fwe_corrected_results.csv")

    df = pd.DataFrame({
        'original_p_value': original_p_values,
        'adjusted_p_value': adjusted_p_values,
        'correction_method': method
    })

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)
    logger.info(f"Saved FWE-corrected results to {output_path}")
    return output_file
