"""
Data Cleaning Module for Sustainable Agriculture Survey Data.

This module handles:
1. Loading raw data (CSV)
2. Calculating missingness metrics
3. Handling missing values (imputation or dropping rows with >30% missing)
4. Normalizing categorical codes
5. Validating the cleaned dataset
6. Power analysis calculation
7. Exporting cleaned data to CSV
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
import numpy as np
import yaml

# Import from project modules
from config import get_config, get_data_path
from logging_config import (
    ReproducibilityLogger,
    get_logger,
    log_operation,
    update_log_section,
    initialize_modeling_log,
    append_log_entry,
)


# Custom error class
class CustomDataError(Exception):
    """Custom exception for data processing errors."""
    pass

@log_operation("load_config")
def load_config_wrapper() -> Dict[str, Any]:
    """Wrapper to load configuration safely."""
    return load_config()

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
def load_raw_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load raw survey data from a CSV file.

    Args:
        input_path: Optional path to the input CSV file. If not provided,
                    uses the path from config.

    Returns:
        pd.DataFrame: The loaded raw data.

    Raises:
        CustomDataError: If the file cannot be loaded or is empty.
    """
    logger = get_logger_instance()
    config = load_config()

    if input_path is None:
        # Try to get from config
        raw_data_path = config.get("paths", {}).get("raw_data", "data/raw/survey_data.csv")
        input_path = raw_data_path

    # Handle relative paths relative to project root
    project_root = Path(__file__).parent.parent
    full_path = project_root / input_path

    if not full_path.exists():
        # Check if it's a relative path from current working directory
        if Path(input_path).exists():
            full_path = Path(input_path)
        else:
            raise CustomDataError(f"Raw data file not found at {input_path}")

    logger.log("load_raw_data", file=str(full_path), status="loading")

    try:
        df = pd.read_csv(full_path)
        if df.empty:
            raise CustomDataError(f"Loaded data file is empty: {input_path}")
        
        logger.log("load_raw_data", status="success", rows=len(df), columns=len(df.columns))
        return df
    except Exception as e:
        logger.log("load_raw_data", status="failed", error=str(e))
        raise CustomDataError(f"Failed to load raw data from {input_path}: {str(e)}")


# ----------------------------------------------------------------------
# Missing Value Analysis
# ----------------------------------------------------------------------

@log_operation("calculate_missingness")
def calculate_missingness(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate missingness metrics for the dataset.

    Args:
        df: Input DataFrame

    Returns:
        Dict containing missingness statistics.
    """
    logger = get_logger_instance()
    logger.log("calculate_missingness", status="starting")

    missing_counts = df.isnull().sum()
    missing_pct = (missing_counts / len(df)) * 100

    # Rows with >30% missing values
    row_missing_pct = df.isnull().mean(axis=1) * 100
    rows_to_drop = row_missing_pct > 30
    num_rows_to_drop = rows_to_drop.sum()

    stats = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "missing_by_column": missing_counts.to_dict(),
        "missing_pct_by_column": missing_pct.to_dict(),
        "rows_with_over_30pct_missing": int(num_rows_to_drop),
        "percentage_rows_to_drop": float(num_rows_to_drop / len(df) * 100),
    }

    logger.log("calculate_missingness", status="success", **stats)
    return stats


# ----------------------------------------------------------------------
# Missing Value Handling
# ----------------------------------------------------------------------

@log_operation("handle_missing_values")
def handle_missing_values(
    df: pd.DataFrame,
    threshold: float = 30.0,
    numeric_imputation: str = "median",
    categorical_imputation: str = "mode"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Handle missing values in the dataset.

    Strategy:
    1. Drop rows where >30% of values are missing.
    2. For remaining rows:
       - Numeric columns: Impute with median (or mean)
       - Categorical columns: Impute with mode (most frequent)

    Args:
        df: Input DataFrame.
        threshold: Percentage threshold for dropping rows (default 30%).
        numeric_imputation: Strategy for numeric imputation ('median' or 'mean').
        categorical_imputation: Strategy for categorical imputation ('mode').

    Returns:
        Tuple of (cleaned DataFrame, imputation stats).
    """
    logger = get_logger_instance()
    logger.log("handle_missing_values", threshold=threshold, status="starting")

    initial_rows = len(df)
    imputation_stats = {
        "initial_rows": initial_rows,
        "columns_imputed": {},
        "rows_dropped": 0,
    }

    # Step 1: Drop rows with >30% missing values
    row_missing_pct = df.isnull().mean(axis=1) * 100
    rows_to_keep = row_missing_pct <= threshold
    df_cleaned = df[rows_to_keep].copy()
    
    rows_dropped = initial_rows - len(df_cleaned)
    imputation_stats["rows_dropped"] = rows_dropped

    if rows_dropped > 0:
        logger.log("handle_missing_values", rows_dropped=rows_dropped, reason=">30% missing")

    # Step 2: Identify numeric and categorical columns
    numeric_cols = df_cleaned.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df_cleaned.select_dtypes(include=["object", "category"]).columns.tolist()

    # Step 3: Impute missing values
    imputed_columns = []

    for col in numeric_cols:
        if df_cleaned[col].isnull().any():
            if numeric_imputation == "median":
                fill_value = df_cleaned[col].median()
            else:
                fill_value = df_cleaned[col].mean()
            
            if pd.isna(fill_value):
                fill_value = 0  # Fallback for all-NaN columns
            
            df_cleaned[col] = df_cleaned[col].fillna(fill_value)
            imputed_columns.append(col)
            imputation_stats["columns_imputed"][col] = {
                "type": "numeric",
                "strategy": numeric_imputation,
                "fill_value": float(fill_value) if not pd.isna(fill_value) else 0.0,
                "missing_count_before": int(df_cleaned[col].isnull().sum()),
            }

    for col in categorical_cols:
        if df_cleaned[col].isnull().any():
            # Mode imputation
            mode_val = df_cleaned[col].mode()
            if len(mode_val) > 0:
                fill_value = mode_val[0]
            else:
                fill_value = "Unknown"
            
            df_cleaned[col] = df_cleaned[col].fillna(fill_value)
            imputed_columns.append(col)
            imputation_stats["columns_imputed"][col] = {
                "type": "categorical",
                "strategy": categorical_imputation,
                "fill_value": str(fill_value),
                "missing_count_before": int(df_cleaned[col].isnull().sum()),
            }

    imputation_stats["columns_imputed_count"] = len(imputed_columns)
    imputation_stats["final_rows"] = len(df_cleaned)

    logger.log("handle_missing_values", status="success", **imputation_stats)
    return df_cleaned, imputation_stats


# ----------------------------------------------------------------------
# Categorical Normalization
# ----------------------------------------------------------------------

@log_operation("normalize_categorical_codes")
def normalize_categorical_codes(
    df: pd.DataFrame,
    code_mappings: Optional[Dict[str, Dict[Any, Any]]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Normalize categorical codes to consistent values.

    This function:
    1. Applies standard mappings for known categorical variables.
    2. Ensures consistent encoding (e.g., "Yes"/"yes"/1 -> 1, "No"/"no"/0 -> 0).
    3. Converts ordinal categories to numeric codes where appropriate.

    Args:
        df: Input DataFrame.
        code_mappings: Optional custom mappings for specific columns.

    Returns:
        Tuple of (normalized DataFrame, normalization stats).
    """
    logger = get_logger_instance()
    logger.log("normalize_categorical_codes", status="starting")

    normalization_stats = {
        "columns_normalized": [],
        "mappings_applied": {},
    }

    # Standard mappings for common categorical variables
    standard_mappings = {
        "adoption": {
            "yes": 1, "Yes": 1, "YES": 1, "Y": 1, "y": 1, 1: 1,
            "no": 0, "No": 0, "NO": 0, "N": 0, "n": 0, 0: 0,
        },
        "gender": {
            "male": 1, "Male": 1, "MALE": 1, "M": 1, "m": 1, 1: 1,
            "female": 0, "Female": 0, "FEMALE": 0, "F": 0, "f": 0, 0: 0,
        },
        "education_level": {
            "none": 0, "None": 0, "No education": 0,
            "primary": 1, "Primary": 1, "Elementary": 1,
            "secondary": 2, "Secondary": 2, "High school": 2,
            "tertiary": 3, "Tertiary": 3, "University": 3, "College": 3,
        },
        "membership": {
            "yes": 1, "Yes": 1, "YES": 1, "Y": 1, "y": 1, 1: 1,
            "no": 0, "No": 0, "NO": 0, "N": 0, "n": 0, 0: 0,
        },
        "extension_contact": {
            "yes": 1, "Yes": 1, "YES": 1, "Y": 1, "y": 1, 1: 1,
            "no": 0, "No": 0, "NO": 0, "N": 0, "n": 0, 0: 0,
        },
    }

    # Merge with custom mappings if provided
    if code_mappings:
        standard_mappings.update(code_mappings)

    df_normalized = df.copy()

    for col, mapping in standard_mappings.items():
        if col in df_normalized.columns:
            original_unique = df_normalized[col].unique().tolist()
            df_normalized[col] = df_normalized[col].map(
                lambda x: mapping.get(x, x) if isinstance(x, (str, int, float)) else x
            )
            
            # Handle unmapped values (keep as is if not in mapping)
            # Convert to numeric if all values are now numeric
            try:
                df_normalized[col] = pd.to_numeric(df_normalized[col], errors="ignore")
            except Exception:
                pass

            normalization_stats["columns_normalized"].append(col)
            normalization_stats["mappings_applied"][col] = {
                "original_values": original_unique[:10],  # First 10 for brevity
                "mapping_size": len(mapping),
            }

    normalization_stats["total_columns_normalized"] = len(normalization_stats["columns_normalized"])
    normalization_stats["final_shape"] = list(df_normalized.shape)

    logger.log("normalize_categorical_codes", status="success", **normalization_stats)
    return df_normalized, normalization_stats


# ----------------------------------------------------------------------
# Data Validation
# ----------------------------------------------------------------------

@log_operation("validate_clean_data")
def validate_clean_data(df: pd.DataFrame, required_columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Validate the cleaned dataset.

    Checks:
    1. No missing values remain (or document them).
    2. Required columns are present.
    3. Data types are appropriate.
    4. Value ranges are reasonable.

    Args:
        df: Input DataFrame.
        required_columns: List of required column names.

    Returns:
        Dict containing validation results.
    """
    logger = get_logger_instance()
    logger.log("validate_clean_data", status="starting")

    validation_results = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "final_stats": {},
    }

    # Default required columns based on the project spec
    if required_columns is None:
        required_columns = [
            "age", "education", "farm_size", "credit_access", 
            "adoption", "adoption_binary", "engagement_score",
            "membership", "extension_contact", "collective_action",
            "knowledge_exchange", "country_code", "household_id"
        ]

    # Check for missing columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        validation_results["errors"].append(f"Missing required columns: {missing_cols}")
        validation_results["is_valid"] = False

    # Check for remaining missing values
    remaining_missing = df.isnull().sum()
    if remaining_missing.sum() > 0:
        validation_results["warnings"].append(
            f"Remaining missing values in {remaining_missing[remaining_missing > 0].to_dict()}"
        )

    # Check for reasonable value ranges
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    for col in numeric_cols:
        if col in df.columns:
            min_val = df[col].min()
            max_val = df[col].max()
            if min_val < 0 and col in ["age", "farm_size", "education"]:
                validation_results["warnings"].append(
                    f"Column '{col}' has negative values (min={min_val})"
                )

    # Final statistics
    validation_results["final_stats"] = {
        "rows": len(df),
        "columns": len(df.columns),
        "total_missing": int(remaining_missing.sum()),
        "required_columns_present": len(missing_cols) == 0,
    }

    if validation_results["is_valid"]:
        logger.log("validate_clean_data", status="success", **validation_results)
    else:
        logger.log("validate_clean_data", status="invalid", **validation_results)

    return validation_results


# ----------------------------------------------------------------------
# Power Analysis
# ----------------------------------------------------------------------

@log_operation("calculate_power_analysis")
def calculate_power_analysis(df: pd.DataFrame, num_predictors: int = 10) -> Dict[str, Any]:
    """
    Calculate power analysis metrics for the dataset.

    Computes the ratio of effective events to predictors (EPV).
    For logistic regression, a rule of thumb is EPV >= 10.

    Args:
        df: Input DataFrame (should contain adoption_binary).
        num_predictors: Number of predictors in the model (default 10).

    Returns:
        Dict containing power analysis results.
    """
    logger = get_logger_instance()
    logger.log("calculate_power_analysis", num_predictors=num_predictors, status="starting")

    power_results = {
        "effective_N_events": 0,
        "num_predictors": num_predictors,
        "ratio": 0.0,
        "shortfall": False,
        "recommendation": "",
    }

    # Try to get effective_N_events from adoption_binary
    if "adoption_binary" in df.columns:
        effective_N_events = df["adoption_binary"].sum()
    elif "adoption" in df.columns:
        # Estimate from adoption column if binary not available
        # Assume adoption is 0/1 or Yes/No
        if df["adoption"].dtype == "object":
            effective_N_events = (df["adoption"].isin(["Yes", "yes", "Y", "1"])).sum()
        else:
            effective_N_events = df["adoption"].sum()
    else:
        # Fallback: estimate as 20% of total rows (conservative)
        effective_N_events = int(len(df) * 0.20)
        power_results["estimation_method"] = "assumed_20pct_adoption"

    power_results["effective_N_events"] = int(effective_N_events)
    ratio = effective_N_events / num_predictors if num_predictors > 0 else 0
    power_results["ratio"] = float(ratio)

    if ratio < 10:
        power_results["shortfall"] = True
        power_results["recommendation"] = (
            f"EPV ({ratio:.1f}) < 10. Consider reducing predictors or collecting more data."
        )
    else:
        power_results["recommendation"] = "EPV is adequate for logistic regression."

    logger.log("calculate_power_analysis", status="success", **power_results)
    return power_results


# ----------------------------------------------------------------------
# Log Updates
# ----------------------------------------------------------------------

@log_operation("update_modeling_log_with_power_analysis")
def update_modeling_log_with_power_analysis(power_results: Dict[str, Any]) -> None:
    """
    Update the modeling log with power analysis results.

    Args:
        power_results: Dictionary from calculate_power_analysis.
    """
    logger = get_logger_instance()
    logger.log("update_modeling_log_with_power_analysis", status="starting")

    try:
        config = load_config()
        project_root = Path(__file__).parent.parent
        log_path = project_root / config.get("paths", {}).get("modeling_log", "modeling_log.yaml")

        if not log_path.exists():
            initialize_modeling_log()

        # Load existing log
        with open(log_path, "r") as f:
            log_data = yaml.safe_load(f) or {}

        # Update power analysis section
        if "power_analysis" not in log_data:
            log_data["power_analysis"] = {}

        log_data["power_analysis"].update({
            "effective_N_events": power_results.get("effective_N_events"),
            "num_predictors": power_results.get("num_predictors"),
            "ratio": power_results.get("ratio"),
            "shortfall": power_results.get("shortfall", False),
            "recommendation": power_results.get("recommendation"),
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Write back
        with open(log_path, "w") as f:
            yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)

        logger.log("update_modeling_log_with_power_analysis", status="success", log_path=str(log_path))
    except Exception as e:
        logger.log("update_modeling_log_with_power_analysis", status="failed", error=str(e))
        # Don't raise - log failure but continue


# ----------------------------------------------------------------------
# Export
# ----------------------------------------------------------------------

@log_operation("export_cleaned_data")
def export_cleaned_data(
    df: pd.DataFrame,
    output_path: Optional[str] = None,
    include_stats: bool = True
) -> str:
    """
    Export cleaned data to CSV.

    Args:
        df: Cleaned DataFrame.
        output_path: Optional output path. If not provided, uses config.
        include_stats: Whether to log export statistics.

    Returns:
        Path to the exported file.
    """
    logger = get_logger_instance()
    logger.log("export_cleaned_data", status="starting")

    if output_path is None:
        config = load_config()
        output_path = config.get("paths", {}).get("cleaned_data", "data/processed/cleaned_data.csv")

    # Handle relative paths
    project_root = Path(__file__).parent.parent
    full_path = project_root / output_path

    # Ensure directory exists
    full_path.parent.mkdir(parents=True, exist_ok=True)

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
    """
    Main entry point for data cleaning pipeline.

    Executes the full cleaning pipeline:
    1. Load raw data
    2. Calculate missingness
    3. Handle missing values
    4. Normalize categorical codes
    5. Validate cleaned data
    6. Calculate power analysis
    7. Export cleaned data
    """
    logger = get_logger_instance()
    logger.log("data_cleaning_main", status="starting")

    try:
        # Initialize modeling log
        initialize_modeling_log()

        # Update log section
        update_log_section("data_cleaning", {"status": "running", "started_at": datetime.utcnow().isoformat()})

        # Step 1: Load raw data
        logger.log("data_cleaning_main", step="load_raw_data")
        raw_df = load_raw_data()
        logger.info(f"Loaded {len(raw_df)} rows")

        # Step 2: Calculate missingness
        logger.log("data_cleaning_main", step="calculate_missingness")
        missingness_stats = calculate_missingness(raw_df)
        logger.info(f"Missingness: {missingness_stats['rows_with_over_30pct_missing']} rows to drop")

        # Step 3: Handle missing values
        logger.log("data_cleaning_main", step="handle_missing_values")
        cleaned_df, imputation_stats = handle_missing_values(raw_df)
        logger.info(f"Imputation complete: {imputation_stats['columns_imputed_count']} columns imputed")

        # Step 4: Normalize categorical codes
        logger.log("data_cleaning_main", step="normalize_categorical_codes")
        normalized_df, norm_stats = normalize_categorical_codes(cleaned_df)
        logger.info(f"Normalization complete: {norm_stats['total_columns_normalized']} columns normalized")

        # Step 5: Validate cleaned data
        logger.log("data_cleaning_main", step="validate_clean_data")
        validation_results = validate_clean_data(normalized_df)
        
        if not validation_results["is_valid"]:
            logger.warning(f"Validation failed: {validation_results['errors']}")
            # Continue anyway, but log warning

        # Step 6: Calculate power analysis
        logger.log("data_cleaning_main", step="calculate_power_analysis")
        power_results = calculate_power_analysis(normalized_df)
        update_modeling_log_with_power_analysis(power_results)
        logger.info(f"Power analysis: EPV = {power_results['ratio']:.1f}")

        # Step 7: Export cleaned data
        logger.log("data_cleaning_main", step="export_cleaned_data")
        output_path = export_cleaned_data(normalized_df)
        logger.info(f"Cleaned data exported to {output_path}")

        # Final log update
        update_log_section("data_cleaning", {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "output_file": output_path,
            "rows_processed": len(normalized_df),
        })

        logger.log("data_cleaning_main", status="success", output_path=output_path)

    except Exception as e:
        error_msg = str(e)
        logger.log("data_cleaning_main", status="failed", error=error_msg)
        update_log_section("data_cleaning", {"status": "failed", "error": error_msg})
        raise CustomDataError(f"Data cleaning failed: {error_msg}")


if __name__ == "__main__":
    main()