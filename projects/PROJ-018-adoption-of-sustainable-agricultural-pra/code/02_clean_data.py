"""Data Cleaning Module for Sustainable Agriculture Survey.

This module handles missing values, normalizes categorical codes, and exports
a cleaned dataset conforming to the project schema.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Import from local modules
from config import get_config
from logging_config import get_logger, log_operation, update_log_section, append_log_entry


class CustomDataError(Exception):
    """Custom exception for data-related errors."""
    pass


def get_logger_instance() -> logging.Logger:
    """Get the project logger instance."""
    return get_logger("data_cleaning")


def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        # Fallback to default paths if config missing
        return {
            "data": {
                "raw_path": "data/raw/survey_data.csv",
                "processed_path": "data/processed/cleaned_data.csv",
                "missing_threshold": 0.30
            },
            "categorical": {
                "education": {"1": "primary", "2": "secondary", "3": "tertiary"},
                "engagement_type": {"1": "formal", "2": "informal", "3": "none"}
            }
        }
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_raw_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """Load raw survey data from CSV.

    Args:
        input_path: Optional path to input file. If None, uses config.

    Returns:
        DataFrame with raw survey data.
    """
    config = load_config()
    path = input_path or config.get("data", {}).get("raw_path", "data/raw/survey_data.csv")

    logger = get_logger_instance()
    logger.info(f"Loading raw data from {path}")

    if not os.path.exists(path):
        raise CustomDataError(f"Raw data file not found: {path}")

    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded {len(df)} records from {path}")
        return df
    except Exception as e:
        raise CustomDataError(f"Failed to load raw data: {str(e)}")


def calculate_missingness(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate missing value percentage per column.

    Args:
        df: Input DataFrame.

    Returns:
        Dictionary mapping column names to missing percentage.
    """
    missing_counts = df.isnull().sum()
    total_rows = len(df)
    if total_rows == 0:
        return {}
    return {col: (count / total_rows) for col, count in missing_counts.items()}


def handle_missing_values(df: pd.DataFrame, threshold: float = 0.30) -> pd.DataFrame:
    """Handle missing values by dropping rows with >threshold missing or imputing.

    Strategy:
    1. Drop rows where >30% of columns are missing.
    2. For remaining rows, impute numerical with median, categorical with mode.

    Args:
        df: Input DataFrame.
        threshold: Maximum allowed missing ratio (default 0.30).

    Returns:
        Cleaned DataFrame.
    """
    logger = get_logger_instance()
    initial_rows = len(df)

    # Calculate missingness
    missingness = calculate_missingness(df)
    logger.info(f"Missingness report: {missingness}")

    # Identify columns with >30% missing globally (drop entirely if needed)
    # For this task, we focus on row-wise filtering as per spec
    # Drop rows where missing ratio > threshold
    row_missing_ratio = df.isnull().sum(axis=1) / df.shape[1]
    mask = row_missing_ratio <= threshold
    df_dropped = df[mask].copy()

    dropped_count = initial_rows - len(df_dropped)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows due to >{threshold*100}% missing values")

    # Impute remaining missing values
    numerical_cols = df_dropped.select_dtypes(include=['number']).columns
    categorical_cols = df_dropped.select_dtypes(include=['object', 'category']).columns

    # Impute numerical with median
    for col in numerical_cols:
        if df_dropped[col].isnull().any():
            median_val = df_dropped[col].median()
            df_dropped[col] = df_dropped[col].fillna(median_val)
            logger.info(f"Imputed numerical column '{col}' with median: {median_val}")

    # Impute categorical with mode
    for col in categorical_cols:
        if df_dropped[col].isnull().any():
            mode_val = df_dropped[col].mode()
            if len(mode_val) > 0:
                fill_val = mode_val[0]
                df_dropped[col] = df_dropped[col].fillna(fill_val)
                logger.info(f"Imputed categorical column '{col}' with mode: {fill_val}")
            else:
                df_dropped[col] = df_dropped[col].fillna("unknown")
                logger.warning(f"Column '{col}' had no mode, filled with 'unknown'")

    return df_dropped


def normalize_categorical_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize categorical codes to standard string labels.

    Maps numeric codes (1, 2, 3...) to readable labels (primary, secondary...)
    based on configuration or default mappings.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with normalized categorical columns.
    """
    logger = get_logger_instance()
    config = load_config()
    cat_mappings = config.get("categorical", {})

    # Default mappings if not in config
    default_mappings = {
        "education": {"1": "primary", "2": "secondary", "3": "tertiary"},
        "engagement_type": {"1": "formal", "2": "informal", "3": "none"},
        "credit_access": {"0": "no", "1": "yes"},
        "adoption_binary": {"0": "no", "1": "yes"}
    }

    merged_mappings = {**default_mappings, **cat_mappings}

    for col, mapping in merged_mappings.items():
        if col in df.columns:
            # Ensure column is string for mapping
            df[col] = df[col].astype(str)
            # Apply mapping, keeping unmapped values as-is
            df[col] = df[col].map(lambda x: mapping.get(x, x))
            logger.info(f"Normalized categorical column '{col}' using mapping")

    return df


def validate_clean_data(df: pd.DataFrame) -> bool:
    """Validate the cleaned dataset.

    Checks:
    - No missing values in required columns
    - Required columns exist

    Args:
        df: Cleaned DataFrame.

    Returns:
        True if valid, raises error otherwise.
    """
    required_cols = ["age", "education", "farm_size", "credit", "adoption"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise CustomDataError(f"Missing required columns: {missing_cols}")

    if df.isnull().any().any():
        cols_with_missing = [col for col in df.columns if df[col].isnull().any()]
        raise CustomDataError(f"Cleaned data still has missing values in: {cols_with_missing}")

    return True


def calculate_power_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate power analysis metrics.

    Computes effective_N_events / num_predictors ratio.
    Returns shortfall info if ratio < 10.

    Args:
        df: Cleaned DataFrame.

    Returns:
        Dictionary with power analysis results.
    """
    logger = get_logger_instance()

    # Estimate number of predictors (excluding ID, target)
    # Assuming binary adoption is target
    target_col = "adoption_binary" if "adoption_binary" in df.columns else None

    if target_col:
        # Count positive outcomes (events)
        effective_N_events = df[target_col].sum() if df[target_col].dtype in ['int64', 'float64'] else (df[target_col] == 1).sum()
    else:
        # Fallback: estimate 10% positive rate if no binary target found
        effective_N_events = len(df) * 0.10
        logger.warning(f"No 'adoption_binary' column found. Estimating events at 10% of N ({effective_N_events:.1f})")

    # Estimate number of predictors (all numeric + categorical columns minus ID/target)
    num_predictors = len([c for c in df.columns if c not in ["id", target_col]])

    if num_predictors == 0:
        ratio = float('inf')
    else:
        ratio = effective_N_events / num_predictors

    result = {
        "effective_N_events": effective_N_events,
        "num_predictors": num_predictors,
        "ratio": ratio,
        "shortfall": ratio < 10
    }

    logger.info(f"Power analysis: {result}")
    return result


def update_modeling_log_with_power_analysis(power_result: Dict[str, Any]) -> None:
    """Update modeling_log.yaml with power analysis results.

    Args:
        power_result: Dictionary from calculate_power_analysis.
    """
    log_path = Path("modeling_log.yaml")
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("modeling:\n  power_analysis: {}\n")

    try:
        with open(log_path, "r") as f:
            log_data = yaml.safe_load(f) or {}

        if "modeling" not in log_data:
            log_data["modeling"] = {}

        log_data["modeling"]["power_analysis"] = power_result

        with open(log_path, "w") as f:
            yaml.dump(log_data, f, default_flow_style=False)

        get_logger_instance().info("Updated modeling_log.yaml with power analysis")
    except Exception as e:
        get_logger_instance().warning(f"Failed to update modeling_log.yaml: {e}")


def export_cleaned_data(df: pd.DataFrame, output_path: Optional[str] = None) -> None:
    """Export cleaned DataFrame to CSV.

    Args:
        df: Cleaned DataFrame.
        output_path: Optional output path. Defaults to config.
    """
    config = load_config()
    path = output_path or config.get("data", {}).get("processed_path", "data/processed/cleaned_data.csv")

    # Ensure directory exists
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(path, index=False)
    get_logger_instance().info(f"Exported cleaned data to {path} ({len(df)} rows)")


@log_operation("data_cleaning_main")
def main(input_path: Optional[str] = None, output_path: Optional[str] = None) -> None:
    """Main entry point for data cleaning pipeline.

    Steps:
    1. Load raw data
    2. Handle missing values (drop >30% missing rows, impute rest)
    3. Normalize categorical codes
    4. Validate cleaned data
    5. Perform power analysis and log to modeling_log.yaml
    6. Export to data/processed/cleaned_data.csv

    Args:
        input_path: Optional input file path.
        output_path: Optional output file path.
    """
    logger = get_logger_instance()
    logger.info("Starting data cleaning pipeline")

    try:
        # 1. Load
        df = load_raw_data(input_path)

        # 2. Handle missing
        config = load_config()
        threshold = config.get("data", {}).get("missing_threshold", 0.30)
        df_clean = handle_missing_values(df, threshold=threshold)

        # 3. Normalize
        df_clean = normalize_categorical_codes(df_clean)

        # 4. Validate
        validate_clean_data(df_clean)

        # 5. Power Analysis
        power_result = calculate_power_analysis(df_clean)
        update_modeling_log_with_power_analysis(power_result)

        # 6. Export
        export_cleaned_data(df_clean, output_path)

        logger.info("Data cleaning pipeline completed successfully")

    except CustomDataError as e:
        logger.error(f"Data error: {str(e)}")
        update_log_section("data_cleaning", {"status": "failed", "error": str(e)})
        append_log_entry({"operation": "data_cleaning", "status": "failed", "error": str(e)})
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        update_log_section("data_cleaning", {"status": "failed", "error": str(e)})
        append_log_entry({"operation": "data_cleaning", "status": "failed", "error": str(e)})
        raise


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Clean survey data")
    parser.add_argument("--input", type=str, help="Input CSV path")
    parser.add_argument("--output", type=str, help="Output CSV path")
    args = parser.parse_args()

    main(input_path=args.input, output_path=args.output)