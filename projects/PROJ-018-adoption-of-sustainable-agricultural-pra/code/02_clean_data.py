"""
Data Cleaning Module for Sustainable Agriculture Survey Data.

This module handles:
- Loading raw data
- Missing value analysis and handling
- Categorical normalization
- Power analysis check (T015)
- Exporting cleaned data
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

# Import from project modules
from config import Config, load_config
from logging_config import (
    LogEntry,
    ReproducibilityLogger,
    append_log_entry,
    get_logger,
    initialize_modeling_log,
    log_operation,
    update_log_section,
)

# Custom exception for data errors
class CustomDataError(Exception):
    """Custom exception for data-related errors."""
    pass


@log_operation("load_config")
def load_config_wrapper(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML file."""
    return load_config(config_path)


# ----------------------------------------------------------------------
# Configuration and Logging Setup
# ----------------------------------------------------------------------

def get_logger_instance() -> ReproducibilityLogger:
    """Get the singleton logger instance."""
    return get_logger("data_cleaning")


def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    config = get_config()
    return config


# ----------------------------------------------------------------------
# Data Loading
# ----------------------------------------------------------------------

@log_operation("load_raw_data")
def load_raw_data(input_path: str) -> pd.DataFrame:
    """
    Load raw data from CSV or JSON.
    
    Args:
        input_path: Path to the raw data file
        
    Returns:
        DataFrame with raw data
        
    Raises:
        CustomDataError: If file cannot be loaded or is empty
    """
    path = Path(input_path)
    if not path.exists():
        raise CustomDataError(f"Input file not found: {input_path}")
    
    if path.suffix.lower() == '.csv':
        df = pd.read_csv(path)
    elif path.suffix.lower() in ['.json']:
        df = pd.read_json(path)
    else:
        raise CustomDataError(f"Unsupported file format: {path.suffix}")
    
    if df.empty:
        raise CustomDataError("Input file is empty")
    
    return df


@log_operation("calculate_missingness")
def calculate_missingness(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate missing value percentage for each column.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary mapping column names to missing percentages
    """
    missing_counts = df.isnull().sum()
    total_rows = len(df)
    if total_rows == 0:
        return {}
    return (missing_counts / total_rows * 100).to_dict()


@log_operation("handle_missing_values")
def handle_missing_values(
    df: pd.DataFrame, 
    threshold: float = 30.0,
    numeric_strategy: str = 'median',
    categorical_strategy: str = 'mode'
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Handle missing values in the DataFrame.
    
    Strategy:
    - Drop rows where > threshold% of required fields are missing
    - Impute remaining missing values based on column type
    
    Args:
        df: Input DataFrame
        threshold: Maximum allowed missing percentage per row (default 30%)
        numeric_strategy: Strategy for numeric columns ('mean', 'median', 'drop')
        categorical_strategy: Strategy for categorical columns ('mode', 'drop', 'unknown')
        
    Returns:
        Tuple of (cleaned DataFrame, imputation log)
    """
    df_clean = df.copy()
    imputation_log = {}
    
    # Identify required columns (based on domain knowledge)
    required_columns = [
        'age', 'education', 'farm_size', 'credit_access', 
        'adoption', 'engagement_score'  # engagement_score may be added later
    ]
    
    # Filter to columns that exist
    existing_required = [col for col in required_columns if col in df_clean.columns]
    
    if not existing_required:
        logging.warning("No required columns found for missing value handling")
        return df_clean, imputation_log
    
    # Calculate missingness per row for required columns
    row_missing_pct = df_clean[existing_required].isnull().sum(axis=1) / len(existing_required) * 100
    
    # Drop rows exceeding threshold
    rows_to_drop = row_missing_pct > threshold
    if rows_to_drop.any():
        dropped_count = rows_to_drop.sum()
        logging.info(f"Dropping {dropped_count} rows with >{threshold}% missing required values")
        imputation_log['rows_dropped'] = int(dropped_count)
        df_clean = df_clean[~rows_to_drop]
    
    # Impute remaining missing values
    for col in df_clean.columns:
        if df_clean[col].isnull().any():
            if pd.api.types.is_numeric_dtype(df_clean[col]):
                if numeric_strategy == 'median':
                  # Handle case where all values are NaN
                  if df_clean[col].notna().sum() == 0:
                      df_clean[col] = 0  # Fallback to 0 if all missing
                  else:
                      df_clean[col] = df_clean[col].fillna(df_clean[col].median())
                elif numeric_strategy == 'mean':
                  if df_clean[col].notna().sum() == 0:
                      df_clean[col] = 0
                  else:
                      df_clean[col] = df_clean[col].fillna(df_clean[col].mean())
                elif numeric_strategy == 'drop':
                  df_clean = df_clean.dropna(subset=[col])
                imputation_log[col] = f"numeric_{numeric_strategy}"
            else:
                if categorical_strategy == 'mode':
                  # Handle case where all values are NaN
                  if df_clean[col].notna().sum() == 0:
                      df_clean[col] = 'unknown'
                  else:
                      mode_val = df_clean[col].mode()
                      if len(mode_val) > 0:
                          df_clean[col] = df_clean[col].fillna(mode_val[0])
                      else:
                          df_clean[col] = 'unknown'
                elif categorical_strategy == 'drop':
                  df_clean = df_clean.dropna(subset=[col])
                elif categorical_strategy == 'unknown':
                  df_clean[col] = df_clean[col].fillna('unknown')
                imputation_log[col] = f"categorical_{categorical_strategy}"
    
    return df_clean, imputation_log


@log_operation("normalize_categorical_codes")
def normalize_categorical_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize categorical codes to standard values.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (normalized DataFrame, normalization stats).
    """
    df_norm = df.copy()
    
    # Common categorical normalizations
    boolean_mappings = {
        'yes': 1, 'no': 0, 'Yes': 1, 'No': 0, 
        'YES': 1, 'NO': 0, 'true': 1, 'false': 0,
        'True': 1, 'False': 0, '1': 1, '0': 0
    }
    
    for col in df_norm.columns:
        if df_norm[col].dtype == 'object':
            # Check if column looks like boolean
            unique_vals = df_norm[col].str.lower().dropna().unique()
            if all(v in ['yes', 'no', 'true', 'false', '1', '0'] for v in unique_vals):
                df_norm[col] = df_norm[col].map(boolean_mappings)
    
    return df_norm


@log_operation("validate_clean_data")
def validate_clean_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate the cleaned data meets requirements.
    
    Args:
        df: Cleaned DataFrame
        
    Returns:
        Validation report dictionary
    """
    report = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'columns': list(df.columns),
        'missing_values': df.isnull().sum().sum(),
        'duplicate_rows': df.duplicated().sum(),
        'dtypes': df.dtypes.astype(str).to_dict()
    }
    
    # Check for negative values in numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if (df[col] < 0).any():
            report[f'negative_{col}'] = int((df[col] < 0).sum())
    
    return report


@log_operation("calculate_power_analysis")
def calculate_power_analysis(
    df: pd.DataFrame, 
    num_predictors: int = 5,
    outcome_col: str = 'adoption_binary'
) -> Dict[str, Any]:
    """
    Calculate power analysis metrics for the dataset.
    
    This implements T015: Calculate effective_N_events / num_predictors.
    If the ratio is < 10, it logs a shortfall.
    
    Args:
        df: Cleaned DataFrame
        num_predictors: Number of predictors in the planned model (default 5)
        outcome_col: Name of the binary outcome column
        
    Returns:
        Dictionary with power analysis results
    """
    result = {
        'effective_N': len(df),
        'num_predictors': num_predictors,
        'outcome_column': outcome_col,
        'shortfall': False,
        'ratio': 0.0
    }
    
    # Determine effective_N_events
    if outcome_col in df.columns:
        # Count positive outcomes (1s) in the binary column
        positive_outcomes = df[outcome_col].sum()
        effective_N_events = int(positive_outcomes)
        logging.info(f"Found {effective_N_events} positive outcomes in '{outcome_col}'")
    else:
        # If outcome column doesn't exist yet, estimate based on a non-negligible proportion
        # We assume a conservative 20% adoption rate for estimation
        estimated_proportion = 0.20
        effective_N_events = int(len(df) * estimated_proportion)
        logging.warning(f"Outcome column '{outcome_col}' not found. Estimating {effective_N_events} events at 20% rate.")
    
    result['effective_N_events'] = effective_N_events
    
    # Calculate ratio
    if num_predictors > 0 and effective_N_events > 0:
        ratio = effective_N_events / num_predictors
        result['ratio'] = round(ratio, 2)
        
        # Check if ratio < 10 (rule of thumb for logistic regression)
        if ratio < 10:
            result['shortfall'] = True
            logging.warning(
                f"Power analysis shortfall detected: ratio={ratio:.2f} < 10. "
                f"Consider collecting more data or reducing predictors."
            )
    
    return result


@log_operation("update_modeling_log_with_power_analysis")
def update_modeling_log_with_power_analysis(
    power_analysis: Dict[str, Any], 
    log_path: str = 'modeling_log.yaml'
) -> None:
    """
    Update the modeling log with power analysis results.
    
    Args:
        power_analysis: Dictionary with power analysis results
        log_path: Path to the modeling log file
    """
    # Initialize or load the log
    log_data = initialize_modeling_log(log_path)
    
    # Add power analysis section
    if 'power_analysis' not in log_data:
        log_data['power_analysis'] = {}
    
    log_data['power_analysis'].update(power_analysis)
    
    # Add limitation note if shortfall exists
    if power_analysis.get('shortfall', False):
        limitations = log_data.get('limitations', [])
        limitation_note = (
            f"Power analysis indicates a shortfall (ratio={power_analysis['ratio']:.2f} < 10). "
            f"This may limit the statistical power of the logistic regression model. "
            f"Interpret results with caution."
        )
        if limitation_note not in limitations:
            limitations.append(limitation_note)
        log_data['limitations'] = limitations
    
    # Write back to file
    with open(log_path, 'w', encoding='utf-8') as f:
        yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)
    
    logging.info(f"Updated modeling log with power analysis at {log_path}")


@log_operation("export_cleaned_data")
def export_cleaned_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Export cleaned data to CSV.
    
    Args:
        df: Cleaned DataFrame
        output_path: Path for output CSV file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logging.info(f"Cleaned data exported to {output_path}")


    # Export to CSV
    df.to_csv(full_path, index=False)

    export_stats = {
        "output_path": str(full_path),
        "rows": len(df),
        "columns": len(df.columns),
        "file_size_bytes": full_path.stat().st_size,
    }

    logger.log("export_cleaned_data", status="success", **export_stats)
    return str(full_path)


# ----------------------------------------------------------------------
# Main Pipeline
# ----------------------------------------------------------------------

@log_operation("data_cleaning_main")
def main() -> None:
    """Main entry point for data cleaning pipeline."""
    parser = argparse.ArgumentParser(description='Clean survey data for analysis')
    parser.add_argument('--input', type=str, default='data/raw/survey_data.csv',
                      help='Path to input raw data file')
    parser.add_argument('--output', type=str, default='data/processed/cleaned_data.csv',
                      help='Path for cleaned data output')
    parser.add_argument('--config', type=str, default='code/config.yaml',
                      help='Path to configuration file')
    parser.add_argument('--missing-threshold', type=float, default=30.0,
                      help='Maximum missing percentage per row (default: 30%)')
    parser.add_argument('--num-predictors', type=int, default=5,
                      help='Number of predictors for power analysis (default: 5)')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = get_logger()
    initialize_modeling_log()
    
    try:
        logging.info("Starting data cleaning pipeline")
        
        # Load configuration
        config = load_config_wrapper(args.config)
        
        # Load raw data
        df_raw = load_raw_data(args.input)
        logging.info(f"Loaded {len(df_raw)} records from {args.input}")
        
        # Calculate initial missingness
        initial_missing = calculate_missingness(df_raw)
        logging.info(f"Initial missingness: {initial_missing}")
        
        # Handle missing values
        df_clean, imputation_log = handle_missing_values(
            df_raw, 
            threshold=args.missing_threshold
        )
        logging.info(f"Imputation log: {imputation_log}")
        
        # Normalize categorical codes
        df_clean = normalize_categorical_codes(df_clean)
        
        # Validate cleaned data
        validation_report = validate_clean_data(df_clean)
        logging.info(f"Validation report: {validation_report}")
        
        # Perform power analysis (T015)
        power_analysis = calculate_power_analysis(
            df_clean, 
            num_predictors=args.num_predictors,
            outcome_col='adoption_binary'
        )
        
        # Update modeling log with power analysis results
        update_modeling_log_with_power_analysis(power_analysis)
        
        # Export cleaned data
        export_cleaned_data(df_clean, args.output)
        
        logging.info("Data cleaning pipeline completed successfully")
        
    except CustomDataError as e:
        logging.error(f"Data error: {str(e)}")
        update_log_section("data_cleaning", {"status": "failed", "error": str(e)})
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        update_log_section("data_cleaning", {"status": "failed", "error": str(e)})
        raise


if __name__ == '__main__':
    main()