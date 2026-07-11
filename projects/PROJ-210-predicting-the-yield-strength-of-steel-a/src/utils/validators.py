"""
Schema validation utilities for raw and processed data.
Ensures data integrity before model training and analysis.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from src.utils.config import THRESHOLDS, PROJECT_ROOT, DATA_RAW_DIR, DATA_PROCESSED_DIR

# Expected schemas based on domain requirements
RAW_DATA_REQUIRED_COLUMNS = {
    "yield_strength": "float",
    "composition_c": "float",
    "composition_mn": "float",
    "composition_cr": "float",
    "composition_ni": "float",
    "heat_treatment_temp": "float",
    "cooling_rate": "float",
    "holding_time": "float"
}

PROCESSED_DATA_REQUIRED_COLUMNS = {
    "yield_strength": "float",
    "composition_c": "float",
    "composition_mn": "float",
    "composition_cr": "float",
    "composition_ni": "float",
    "heat_treatment_temp": "float",
    "cooling_rate": "float",
    "holding_time": "float",
    "c_mn_ratio": "float",
    "cr_ni_ratio": "float",
    "cooling_rate_holding_time_interaction": "float",
    "c_cooling_rate_interaction": "float"
}

def validate_schema(df: pd.DataFrame, schema: Dict[str, str], name: str = "Data") -> Tuple[bool, List[str]]:
    """
    Validate that a DataFrame matches the expected schema (columns and types).

    Args:
        df: The DataFrame to validate.
        schema: Dictionary mapping column names to expected dtype strings.
        name: Human-readable name for the data being validated.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []
    if df is None:
        return False, ["DataFrame is None"]

    if df.empty:
        return False, ["DataFrame is empty"]

    # Check for missing columns
    required_cols = set(schema.keys())
    present_cols = set(df.columns)
    missing_cols = required_cols - present_cols

    if missing_cols:
        errors.append(f"Missing required columns in {name}: {missing_cols}")

    # Check for unexpected columns (optional strictness, here we just log)
    extra_cols = present_cols - required_cols
    if extra_cols:
        errors.append(f"Warning: Extra columns in {name}: {extra_cols}")

    # Check types for present required columns
    for col, expected_type in schema.items():
        if col in present_cols:
            actual_type = df[col].dtype
            # Basic type checking
            if expected_type == "float":
                if not np.issubdtype(actual_type, np.floating):
                    # Allow integer to be castable to float, but warn if object
                    if actual_type == object:
                        errors.append(f"Column '{col}' in {name} has type '{actual_type}', expected float.")
                    elif not np.issubdtype(actual_type, np.number):
                        errors.append(f"Column '{col}' in {name} has type '{actual_type}', expected float.")

    return len(errors) == 0, errors

def validate_raw_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate raw data against the raw schema.
    Specifically checks for missing yield strength values (FR-001).
    """
    is_valid, errors = validate_schema(df, RAW_DATA_REQUIRED_COLUMNS, "Raw Data")

    if "yield_strength" in df.columns:
        if df["yield_strength"].isnull().any():
            errors.append("Raw data contains missing values in 'yield_strength' column (FR-001 violation).")
            is_valid = False

    return is_valid, errors

def validate_processed_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate processed data against the processed schema.
    Checks for nulls in target and derived features.
    """
    is_valid, errors = validate_schema(df, PROCESSED_DATA_REQUIRED_COLUMNS, "Processed Data")

    # Check for nulls in target
    if "yield_strength" in df.columns:
        if df["yield_strength"].isnull().any():
            errors.append("Processed data contains missing values in 'yield_strength' column.")
            is_valid = False

    # Check for nulls in derived features (should not exist after cleaning)
    derived_cols = [c for c in df.columns if c not in RAW_DATA_REQUIRED_COLUMNS.keys()]
    for col in derived_cols:
        if df[col].isnull().any():
            errors.append(f"Processed data contains missing values in derived column '{col}'.")
            is_valid = False

    return is_valid, errors

def check_missing_values(df: pd.DataFrame, threshold: float = 0.0) -> Dict[str, float]:
    """
    Check for missing values in each column and return the percentage.

    Args:
        df: The DataFrame to check.
        threshold: If percentage > threshold, flag it.

    Returns:
        Dictionary mapping column names to missing percentage.
    """
    if df is None or df.empty:
        return {}

    missing_pct = (df.isnull().sum() / len(df)) * 100
    return missing_pct.to_dict()

def validate_data_load(file_path: str) -> Tuple[bool, List[str]]:
    """
    Validate that a file can be loaded and has non-zero rows.
    """
    errors = []
    if not os.path.exists(file_path):
        return False, [f"File not found: {file_path}"]

    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".parquet"):
            df = pd.read_parquet(file_path)
        else:
            return False, [f"Unsupported file format: {file_path}"]

        if df.empty:
            errors.append("Loaded file is empty.")
            return False, errors

        return True, []
    except Exception as e:
        return False, [f"Error loading file: {str(e)}"]

def get_data_quality_report(df: pd.DataFrame, name: str = "Data") -> str:
    """
    Generate a text report on data quality.
    """
    lines = [f"Data Quality Report: {name}"]
    lines.append(f"Shape: {df.shape}")
    lines.append(f"Columns: {list(df.columns)}")

    missing = check_missing_values(df)
    high_missing = {k: v for k, v in missing.items() if v > 0}
    if high_missing:
        lines.append(f"Columns with missing values: {high_missing}")
    else:
        lines.append("No missing values found.")

    # Check dtypes
    lines.append("Dtypes:")
    for col, dtype in df.dtypes.items():
        lines.append(f"  {col}: {dtype}")

    return "\n".join(lines)
