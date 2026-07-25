"""
Collinearity diagnostics for the resting-state fMRI global signal analysis.

Implements Variance Inflation Factor (VIF) calculation and correlation analysis
between Global Signal Amplitude (GSA) and Framewise Displacement (FD).

Input: data/processed/cleaned_data.csv
Output: data/results/diagnostics.json
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import shared utilities
from utils import get_logger, write_json, ensure_file_directory
from config import ensure_directories

logger = get_logger(__name__)


def calculate_vif(df: pd.DataFrame, feature_names: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for a list of features.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the features.
    feature_names : List[str]
        List of column names to calculate VIF for.

    Returns
    -------
    Dict[str, float]
        Dictionary mapping feature names to their VIF values.
    """
    X = df[feature_names].values
    
    # Add intercept column for VIF calculation
    X_with_intercept = np.column_stack((np.ones(X.shape[0]), X))
    
    vif_data = {}
    for i, name in enumerate(feature_names):
        # VIF for feature i is the VIF of the i-th column in the design matrix
        # (skipping the intercept which is at index 0)
        try:
            vif = variance_inflation_factor(X_with_intercept, i + 1)
            vif_data[name] = float(vif)
        except Exception as e:
            logger.error(f"Error calculating VIF for {name}: {e}")
            vif_data[name] = float('inf')
    
    return vif_data


def calculate_correlation(df: pd.DataFrame, col1: str, col2: str) -> float:
    """
    Calculate Pearson correlation between two columns.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the columns.
    col1 : str
        First column name.
    col2 : str
        Second column name.

    Returns
    -------
    float
        Pearson correlation coefficient.
    """
    valid_rows = df[[col1, col2]].dropna()
    if len(valid_rows) < 2:
        logger.warning(f"Not enough valid rows to calculate correlation between {col1} and {col2}")
        return 0.0
    
    correlation = valid_rows[col1].corr(valid_rows[col2])
    return float(correlation)


def run_collinearity_diagnostics(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run full collinearity diagnostics on the cleaned dataset.

    Parameters
    ----------
    input_path : str
        Path to the input cleaned_data.csv.
    output_path : str
        Path to save the diagnostics.json output.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing diagnostic results.
    """
    logger.info(f"Loading data from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} subjects")
    
    # Define predictors for the main model: Y ~ Global_Signal_SD + FD + DVARS + Age + Sex
    predictors = ['Global_Signal_SD', 'Mean_FD', 'Mean_DVARS', 'Age', 'Sex']
    
    # Validate that all required columns exist
    missing_cols = [col for col in predictors if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for diagnostics: {missing_cols}")
    
    # Calculate VIF for all predictors
    logger.info("Calculating Variance Inflation Factors (VIF)...")
    vif_results = calculate_vif(df, predictors)
    
    # Flag high collinearity (VIF > 5)
    high_vif_features = [name for name, vif in vif_results.items() if vif > 5]
    if high_vif_features:
        logger.warning(f"High collinearity detected (VIF > 5) for features: {high_vif_features}")
    else:
        logger.info("No features with VIF > 5 detected.")
    
    # Calculate correlation between Global Signal SD and FD
    logger.info("Calculating GSA-FD correlation...")
    gs_fd_corr = calculate_correlation(df, 'Global_Signal_SD', 'Mean_FD')
    
    # Prepare results dictionary
    results = {
        "vif": vif_results,
        "high_vif_features": high_vif_features,
        "gs_fd_correlation": gs_fd_corr,
        "n_subjects": len(df),
        "threshold_vif": 5.0,
        "status": "warning" if high_vif_features else "ok"
    }
    
    # Ensure output directory exists
    ensure_file_directory(output_path)
    
    # Write results to JSON
    logger.info(f"Writing diagnostics to {output_path}")
    write_json(output_path, results)
    
    return results


def main():
    """Main entry point for collinearity diagnostics."""
    # Ensure project directories are set up
    ensure_directories()
    
    input_file = "data/processed/cleaned_data.csv"
    output_file = "data/results/diagnostics.json"
    
    try:
        results = run_collinearity_diagnostics(input_file, output_file)
        logger.info("Collinearity diagnostics completed successfully.")
        logger.info(f"VIF Results: {results['vif']}")
        logger.info(f"GSA-FD Correlation: {results['gs_fd_correlation']:.4f}")
        
        if results['high_vif_features']:
            logger.warning(f"High collinearity found in: {', '.join(results['high_vif_features'])}")
        
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during diagnostics: {e}")
        raise


if __name__ == "__main__":
    main()
