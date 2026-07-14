"""
Data Cleaning Pipeline for Sustainable Agriculture Survey Data.

This module handles:
1. Loading raw data
2. Calculating and handling missing values
3. Normalizing categorical codes
4. Validating the cleaned dataset
5. Performing power analysis checks
6. Exporting cleaned data
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np
import yaml

# Import from local modules
from config import load_config, get_processed_data_path, get_raw_data_path
from logging_config import log_operation, update_log_section, get_logger

# Custom error class
class CustomDataError(Exception):
    """Custom exception for data processing errors."""
    pass

@log_operation("load_config")
def load_config_wrapper() -> Dict[str, Any]:
    """Wrapper to load configuration safely."""
    return load_config()

@log_operation("load_raw_data")
def load_raw_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load raw data from CSV or JSON.

    Args:
        input_path: Optional path to input file. If None, uses config.

    Returns:
        pd.DataFrame: Loaded dataset
    """
    config = load_config_wrapper()
    if input_path is None:
        input_path = config.get("raw_data_path", str(get_raw_data_path() / "survey_data.csv"))

    path = Path(input_path)
    if not path.exists():
        raise CustomDataError(f"Input file not found: {input_path}")

    try:
        if path.suffix == '.csv':
            df = pd.read_csv(path)
        elif path.suffix == '.json':
            df = pd.read_json(path)
        else:
            raise CustomDataError(f"Unsupported file format: {path.suffix}")

        logging.info(f"Loaded {len(df)} records from {input_path}")
        return df
    except Exception as e:
        raise CustomDataError(f"Failed to load data: {str(e)}") from e

@log_operation("calculate_missingness")
def calculate_missingness(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate missingness percentage for each column.

    Args:
        df: Input DataFrame

    Returns:
        Dict mapping column names to missingness percentages
    """
    missing_counts = df.isna().sum()
    total_rows = len(df)
    if total_rows == 0:
        return {}
    return {col: (count / total_rows) * 100 for col, count in missing_counts.items()}

@log_operation("handle_missing_values")
def handle_missing_values(
    df: pd.DataFrame,
    threshold: float = 30.0,
    numeric_strategy: str = "mean",
    categorical_strategy: str = "mode"
) -> pd.DataFrame:
    """
    Handle missing values based on column type and missingness threshold.

    Args:
        df: Input DataFrame
        threshold: Maximum allowed missingness percentage (default 30%)
        numeric_strategy: Strategy for numeric columns ('mean', 'median', 'drop')
        categorical_strategy: Strategy for categorical columns ('mode', 'drop')

    Returns:
        Cleaned DataFrame
    """
    df_clean = df.copy()
    missingness = calculate_missingness(df_clean)

    cols_to_drop = []
    for col, pct in missingness.items():
        if pct > threshold:
            cols_to_drop.append(col)
            logging.warning(f"Dropping column '{col}' due to {pct:.1f}% missingness")

    if cols_to_drop:
        df_clean = df_clean.drop(columns=cols_to_drop)

    # Handle remaining missing values
    for col in df_clean.columns:
        if df_clean[col].isna().any():
            if pd.api.types.is_numeric_dtype(df_clean[col]):
                if numeric_strategy == "mean":
                    df_clean[col] = df_clean[col].fillna(df_clean[col].mean())
                elif numeric_strategy == "median":
                    df_clean[col] = df_clean[col].fillna(df_clean[col].median())
                elif numeric_strategy == "drop":
                    df_clean = df_clean.dropna(subset=[col])
            else:
                if categorical_strategy == "mode":
                    mode_val = df_clean[col].mode()
                    if len(mode_val) > 0:
                        df_clean[col] = df_clean[col].fillna(mode_val[0])
                    else:
                        df_clean[col] = df_clean[col].fillna("Unknown")
                elif categorical_strategy == "drop":
                    df_clean = df_clean.dropna(subset=[col])

    return df_clean

@log_operation("normalize_categorical_codes")
def normalize_categorical_codes(df: pd.DataFrame, mapping_dict: Optional[Dict[str, Dict]] = None) -> pd.DataFrame:
    """
    Normalize categorical codes to standard values.

    Args:
        df: Input DataFrame
        mapping_dict: Optional dict mapping column names to value mappings

    Returns:
        DataFrame with normalized categorical values
    """
    df_norm = df.copy()

    # Default mappings for common fields
    default_mappings = {
        "education": {
            "1": "primary", "2": "secondary", "3": "tertiary",
            "primary": "primary", "secondary": "secondary", "tertiary": "tertiary"
        },
        "engagement_level": {
            "1": "low", "2": "medium", "3": "high",
            "low": "low", "medium": "medium", "high": "high"
        }
    }

    mappings = mapping_dict or default_mappings

    for col, mapping in mappings.items():
        if col in df_norm.columns:
            df_norm[col] = df_norm[col].map(lambda x: mapping.get(str(x), x))
            logging.debug(f"Normalized column '{col}' with {len(mapping)} mappings")

    return df_norm

@log_operation("validate_clean_data")
def validate_clean_data(df: pd.DataFrame, required_columns: Optional[List[str]] = None) -> bool:
    """
    Validate that the cleaned data meets requirements.

    Args:
        df: Cleaned DataFrame
        required_columns: List of required column names

    Returns:
        True if validation passes, False otherwise
    """
    required = required_columns or [
        "age", "education", "farm_size", "credit_access",
        "adoption", "engagement"
    ]

    missing_cols = [col for col in required if col not in df.columns]
    if missing_cols:
        logging.error(f"Missing required columns: {missing_cols}")
        return False

    # Check for remaining missing values in required columns
    for col in required:
        if col in df.columns and df[col].isna().any():
            logging.error(f"Column '{col}' still has missing values after cleaning")
            return False

    logging.info(f"Validation passed for {len(df)} records with {len(df.columns)} columns")
    return True

@log_operation("calculate_power_analysis")
def calculate_power_analysis(df: pd.DataFrame, num_predictors: int = 5) -> Dict[str, Any]:
    """
    Calculate power analysis metrics to assess statistical power.

    This function calculates the ratio of effective events (positive outcomes)
    to the number of predictors. A ratio < 10 indicates a potential power shortfall.

    Args:
        df: Cleaned DataFrame containing adoption data
        num_predictors: Estimated number of predictors in the model (default 5)

    Returns:
        Dict with power analysis results:
            - effective_N_events: Count of positive outcomes
            - num_predictors: Number of predictors
            - ratio: Events per predictor ratio
            - shortfall: Boolean indicating if ratio < 10
    """
    effective_N_events = 0

    # Try to find adoption_binary column first
    if "adoption_binary" in df.columns:
        effective_N_events = int(df["adoption_binary"].sum())
        logging.info(f"Found 'adoption_binary' column. Positive outcomes: {effective_N_events}")
    # Fallback: check for 'adoption' column and estimate if it's binary-like
    elif "adoption" in df.columns:
        if df["adoption"].dtype in ['int64', 'float64']:
            # If numeric, assume 1 indicates adoption
            effective_N_events = int((df["adoption"] > 0).sum())
        elif df["adoption"].dtype == 'object':
            # If object, count non-null as adoption if we assume presence = adoption
            # Or count specific values if known. Here we count non-null as a conservative estimate
            # if the column represents a practice count, we might need a threshold.
            # For power analysis, we need a binary outcome.
            # If 'adoption' is a count of practices, we assume adoption_binary = count > 0
            effective_N_events = int((df["adoption"] > 0).sum())
        logging.info(f"Estimated positive outcomes from 'adoption' column: {effective_N_events}")
    else:
        # If no adoption column, estimate a non-negligible proportion (e.g., 20% of N)
        # This is a conservative estimate for planning purposes only.
        effective_N_events = int(len(df) * 0.20)
        logging.warning(f"No adoption column found. Estimated positive outcomes as 20% of N: {effective_N_events}")

    ratio = effective_N_events / num_predictors if num_predictors > 0 else float('inf')
    shortfall = ratio < 10

    result = {
        "effective_N_events": effective_N_events,
        "num_predictors": num_predictors,
        "ratio": round(ratio, 2),
        "shortfall": shortfall
    }

    logging.info(f"Power Analysis: {effective_N_events} events / {num_predictors} predictors = {ratio:.2f}")
    if shortfall:
        logging.warning(f"POWER SHORTFALL: Ratio ({ratio:.2f}) is below recommended threshold of 10.")

    return result

@log_operation("update_modeling_log_with_power_analysis")
def update_modeling_log_with_power_analysis(power_results: Dict[str, Any]) -> None:
    """
    Update the modeling_log.yaml with power analysis results.

    Args:
        power_results: Dictionary containing power analysis metrics
    """
    config = load_config_wrapper()
    log_path = Path(config.get("modeling_log_path", "modeling_log.yaml"))

    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing log or create new
    if log_path.exists():
        with open(log_path, 'r', encoding='utf-8') as f:
            try:
                log_data = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                log_data = {}
    else:
        log_data = {}

    # Update power analysis section
    if "power_analysis" not in log_data:
        log_data["power_analysis"] = {}

    log_data["power_analysis"].update(power_results)
    log_data["power_analysis"]["timestamp"] = pd.Timestamp.utcnow().isoformat()

    # Document limitation if shortfall exists (per SC-006)
    if power_results.get("shortfall", False):
        limitations = log_data.get("limitations", [])
        limitation_entry = {
            "type": "power_shortfall",
            "description": f"Events per predictor ratio ({power_results['ratio']:.2f}) is below recommended threshold of 10. "
                           "Results should be interpreted with caution regarding statistical power.",
            "timestamp": pd.Timestamp.utcnow().isoformat()
        }
        if limitation_entry not in limitations:
            limitations.append(limitation_entry)
        log_data["limitations"] = limitations
        logging.info("Documented power shortfall as study limitation in modeling_log.yaml")

    # Write back to file
    with open(log_path, 'w', encoding='utf-8') as f:
        yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)

    logging.info(f"Updated modeling log at {log_path} with power analysis results")

@log_operation("export_cleaned_data")
def export_cleaned_data(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """
    Export cleaned data to CSV.

    Args:
        df: Cleaned DataFrame
        output_path: Optional output path. If None, uses config.

    Returns:
        Path to the exported file
    """
    config = load_config_wrapper()
    if output_path is None:
        output_path = str(Path(config.get("processed_data_path", str(get_processed_data_path()))) / "cleaned_data.csv")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(path, index=False)
    logging.info(f"Exported cleaned data to {output_path} ({len(df)} records)")
    return str(path)

@log_operation("main")
def main() -> None:
    """Main entry point for data cleaning pipeline."""
    parser = argparse.ArgumentParser(description="Clean survey data for analysis")
    parser.add_argument("--input", type=str, help="Path to input data file")
    parser.add_argument("--output", type=str, help="Path to output cleaned data file")
    parser.add_argument("--threshold", type=float, default=30.0, help="Missingness threshold (%)")
    args = parser.parse_args()

    try:
        # Load raw data
        df_raw = load_raw_data(args.input)
        logging.info(f"Loaded {len(df_raw)} raw records")

        # Handle missing values
        df_clean = handle_missing_values(df_raw, threshold=args.threshold)
        logging.info(f"After missing value handling: {len(df_clean)} records")

        # Normalize categorical codes
        df_clean = normalize_categorical_codes(df_clean)

        # Validate cleaned data
        if not validate_clean_data(df_clean):
            raise CustomDataError("Validation failed after cleaning")

        # Perform power analysis
        power_results = calculate_power_analysis(df_clean, num_predictors=5)
        update_modeling_log_with_power_analysis(power_results)

        # Export cleaned data
        output_path = export_cleaned_data(df_clean, args.output)

        logging.info("Data cleaning pipeline completed successfully")
        print(f"Cleaned data saved to: {output_path}")

    except CustomDataError as e:
        logging.error(f"Data cleaning failed: {str(e)}")
        update_log_section("data_cleaning", {"status": "failed", "error": str(e)})
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error during data cleaning: {str(e)}")
        update_log_section("data_cleaning", {"status": "failed", "error": str(e)})
        sys.exit(1)

if __name__ == "__main__":
    main()