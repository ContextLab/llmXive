"""
02_clean_data.py - Data Cleaning and Power Analysis

This script performs data cleaning operations on the raw survey data:
1. Handles missing values (imputation or dropping rows with >30% missing)
2. Normalizes categorical codes
3. Calculates power analysis metrics
4. Exports cleaned data to data/processed/cleaned_data.csv
5. Updates modeling_log.yaml with power analysis results
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import Config, load_config_from_yaml, get_config, set_random_seed
from logging_config import (
    LogEntry,
    get_logger,
    initialize_modeling_log,
    update_log_section,
    append_log_entry,
    log_operation,
)

# Define required variables for validation
REQUIRED_VARIABLES = [
    "age",
    "education",
    "farm_size",
    "credit_access",
    "adoption",
    "engagement_membership",
    "engagement_extension",
    "engagement_collective_action",
    "engagement_knowledge_exchange",
]

# Engagement proxy variables for score calculation
ENGAGEMENT_PROXIES = [
    "engagement_membership",
    "engagement_extension",
    "engagement_collective_action",
    "engagement_knowledge_exchange",
]

class CustomDataError(Exception):
    """Custom exception for data-related errors."""
    pass

def load_config() -> Config:
    """Load configuration from YAML file."""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        # Create default config if not exists
        default_config = {
            "random_seed": 42,
            "raw_data_path": "data/raw/survey_data.csv",
            "processed_data_path": "data/processed",
            "project_root": ".",
            "modeling_log_path": "modeling_log.yaml",
        }
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(default_config, f)
    return load_config_from_yaml(str(config_path))

def map_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """Map common alias column names to standard names."""
    alias_map = {
        "farmsize": "farm_size",
        "credits": "credit_access",
        "adopted": "adoption",
        "membership": "engagement_membership",
        "extension_contact": "engagement_extension",
        "collective": "engagement_collective_action",
        "knowledge": "engagement_knowledge_exchange",
    }
    for alias, standard in alias_map.items():
        if alias in df.columns and standard not in df.columns:
            df[standard] = df[alias]
    return df

def validate_variables(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that required variables are present in the dataset.

    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (is_valid, list_of_missing_variables)
    """
    missing_vars = []
    for var in REQUIRED_VARIABLES:
        if var not in df.columns:
            missing_vars.append(var)

    if missing_vars:
        logging.warning(f"Missing required variables: {missing_vars}")
        return False, missing_vars
    return True, []

def calculate_missingness(df: pd.DataFrame) -> pd.Series:
    """Calculate the percentage of missing values per column."""
    return df.isnull().mean() * 100

def handle_missing_values(
    df: pd.DataFrame, threshold: float = 30.0
) -> pd.DataFrame:
    """
    Handle missing values in the dataset.

    Strategy:
    - For columns with > threshold% missing, drop the column
    - For remaining columns, impute numeric with median, categorical with mode
    - Drop rows that still have > threshold% missing values

    Args:
        df: Input DataFrame
        threshold: Maximum percentage of missing values allowed (default 30%)

    Returns:
        Cleaned DataFrame
    """
    df_clean = df.copy()

    # Calculate missingness
    missingness = calculate_missingness(df_clean)

    # Drop columns with too much missing data
    cols_to_drop = missingness[missingness > threshold].index.tolist()
    if cols_to_drop:
        logging.info(f"Dropping columns with >{threshold}% missing: {cols_to_drop}")
        df_clean = df_clean.drop(columns=cols_to_drop)

    # Identify numeric and categorical columns
    numeric_cols = df_clean.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df_clean.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    # Impute numeric columns with median
    for col in numeric_cols:
        median_val = df_clean[col].median()
        if pd.isna(median_val):
            median_val = 0
        df_clean[col] = df_clean[col].fillna(median_val)

    # Impute categorical columns with mode
    for col in categorical_cols:
        mode_val = df_clean[col].mode()
        if len(mode_val) > 0:
            df_clean[col] = df_clean[col].fillna(mode_val[0])
        else:
            df_clean[col] = df_clean[col].fillna("Unknown")

    # Drop rows with > threshold% missing values
    row_missingness = df_clean.isnull().mean(axis=1) * 100
    rows_to_drop = row_missingness[row_missingness > threshold].index.tolist()
    if rows_to_drop:
        logging.info(f"Dropping {len(rows_to_drop)} rows with >{threshold}% missing")
        df_clean = df_clean.drop(index=rows_to_drop)

    return df_clean

def normalize_categorical_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize categorical codes to standard values.

    Maps common variations to standard numeric codes:
    - Yes/True/1 -> 1
    - No/False/0 -> 0
    - Other string values are encoded as unique integers

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with normalized categorical codes
    """
    df_clean = df.copy()

    # Define boolean-like mappings
    yes_values = ["yes", "y", "true", "1", 1, True]
    no_values = ["no", "n", "false", "0", 0, False]

    categorical_cols = df_clean.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    for col in categorical_cols:
        # Check if column looks binary
        unique_vals = df_clean[col].unique()
        if len(unique_vals) <= 2:
            # Try to map to binary
            mapped_vals = []
            for val in df_clean[col]:
                if val in yes_values:
                    mapped_vals.append(1)
                elif val in no_values:
                    mapped_vals.append(0)
                else:
                    mapped_vals.append(val)
            df_clean[col] = mapped_vals

        # For non-binary categorical, use label encoding
        else:
            unique_sorted = sorted(df_clean[col].dropna().unique())
            label_map = {val: idx for idx, val in enumerate(unique_sorted)}
            df_clean[col] = df_clean[col].map(label_map).fillna(-1)

    return df_clean

def calculate_power_analysis(
    df: pd.DataFrame, num_predictors: int = 10
) -> Dict[str, Any]:
    """
    Calculate power analysis metrics for the dataset.

    Computes effective_N_events / num_predictors ratio.
    effective_N_events is the count of positive outcomes in adoption_binary
    if available, or estimated as a proportion of N if not.

    Args:
        df: Input DataFrame (should contain adoption_binary if available)
        num_predictors: Number of predictors in the planned model (default 10)

    Returns:
        Dictionary with power analysis results
    """
    n_total = len(df)

    # Try to get adoption_binary column
    if "adoption_binary" in df.columns:
        effective_n_events = df["adoption_binary"].sum()
    elif "adoption" in df.columns:
        # Estimate from adoption column if binary not yet created
        # Assume non-zero adoption indicates positive outcome
        effective_n_events = (df["adoption"] > 0).sum()
    else:
        # Fallback: estimate 20% adoption rate as a reasonable assumption
        # This is a conservative estimate for power analysis purposes
        effective_n_events = int(n_total * 0.20)
        logging.warning(
            f"No adoption_binary or adoption column found. "
            f"Estimating effective_N_events as {effective_n_events} "
            f"(20% of {n_total}) for power analysis."
        )

    ratio = effective_n_events / num_predictors if num_predictors > 0 else float("inf")

    return {
        "n_total": n_total,
        "effective_n_events": int(effective_n_events),
        "num_predictors": num_predictors,
        "ratio": round(ratio, 2),
        "shortfall": ratio < 10,
    }

def update_modeling_log_with_power_analysis(
    log_path: Path, power_results: Dict[str, Any]
) -> None:
    """
    Update modeling_log.yaml with power analysis results.

    Args:
        log_path: Path to modeling_log.yaml
        power_results: Dictionary with power analysis metrics
    """
    log_data = {}
    if log_path.exists():
        with open(log_path, "r") as f:
            log_data = yaml.safe_load(f) or {}

    # Update power_analysis section
    log_data["power_analysis"] = power_results

    with open(log_path, "w") as f:
        yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)

    logging.info(f"Updated power analysis in {log_path}")

@log_operation("data_acquisition_main")
def load_raw_data(config: Config) -> pd.DataFrame:
    """Load raw data from the configured path."""
    raw_path = Path(config.get("raw_data_path", "data/raw/survey_data.csv"))
    if not raw_path.exists():
        raise CustomDataError(f"Raw data file not found: {raw_path}")

    df = pd.read_csv(raw_path)
    logging.info(f"Loaded {len(df)} records from {raw_path}")
    return df

@log_operation("data_validation_main")
def validate_clean_data(df: pd.DataFrame) -> bool:
    """Validate that cleaned data meets requirements."""
    is_valid, missing = validate_variables(df)
    if not is_valid:
        raise CustomDataError(f"Data validation failed. Missing: {missing}")
    return True

@log_operation("data_export_main")
def export_cleaned_data(df: pd.DataFrame, output_path: Path) -> None:
    """Export cleaned data to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info(f"Exported {len(df)} cleaned records to {output_path}")

def main():
    """Main entry point for data cleaning pipeline."""
    parser = argparse.ArgumentParser(description="Clean survey data for analysis")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input CSV file (overrides config)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output CSV file (overrides config)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=30.0,
        help="Missing value threshold percentage (default: 30)",
    )
    parser.add_argument(
        "--predictors",
        type=int,
        default=10,
        help="Number of predictors for power analysis (default: 10)",
    )
    args = parser.parse_args()

    # Initialize logging
    config = load_config()
    set_random_seed(config.get("random_seed", 42))

    # Initialize modeling log
    log_path = Path(config.get("modeling_log_path", "modeling_log.yaml"))
    initialize_modeling_log(log_path)

    logging.info("Starting data cleaning pipeline")
    update_log_section(
        "data_cleaning",
        {"status": "started", "timestamp": datetime.utcnow().isoformat()},
    )

    try:
        # Load raw data
        if args.input:
            raw_path = Path(args.input)
        else:
            raw_path = Path(config.get("raw_data_path", "data/raw/survey_data.csv"))

        if not raw_path.exists():
            raise CustomDataError(f"Input file not found: {raw_path}")

        df = pd.read_csv(raw_path)
        logging.info(f"Loaded {len(df)} records from {raw_path}")

        # Map aliases
        df = map_aliases(df)

        # Validate variables
        is_valid, missing = validate_variables(df)
        if not is_valid:
            logging.warning(f"Missing required variables: {missing}")
            update_log_section(
                "data_acquisition",
                {"status": "validation_failed", "missing_variables": missing},
            )
            # Continue anyway - we'll handle missing in cleaning

        # Handle missing values
        df = handle_missing_values(df, threshold=args.threshold)
        logging.info(f"After missing value handling: {len(df)} records")

        # Normalize categorical codes
        df = normalize_categorical_codes(df)

        # Validate cleaned data
        validate_clean_data(df)

        # Calculate power analysis
        power_results = calculate_power_analysis(df, num_predictors=args.predictors)
        logging.info(f"Power analysis: ratio={power_results['ratio']}, shortfall={power_results['shortfall']}")

        # Update modeling log with power analysis
        update_modeling_log_with_power_analysis(log_path, power_results)

        # Export cleaned data
        if args.output:
            output_path = Path(args.output)
        else:
            output_dir = Path(config.get("processed_data_path", "data/processed"))
            output_path = output_dir / "cleaned_data.csv"

        export_cleaned_data(df, output_path)

        update_log_section(
            "data_cleaning",
            {
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat(),
                "records_processed": len(df),
                "power_analysis": power_results,
            },
        )

        logging.info("Data cleaning pipeline completed successfully")

    except Exception as e:
        error_msg = str(e)
        logging.error(f"Data cleaning failed: {error_msg}")
        update_log_section(
            "data_cleaning",
            {"status": "failed", "error": error_msg},
        )
        raise CustomDataError(error_msg) from e

if __name__ == '__main__':
    main()