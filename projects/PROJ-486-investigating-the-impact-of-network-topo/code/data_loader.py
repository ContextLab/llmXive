"""
Data loading and validation utilities for the network topology entrainment project.
"""
import os
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any

# Required columns for entrainment data (FR-008)
REQUIRED_ENTRAINMENT_COLUMNS = {'subject_id', 'entrainment_metric'}

# Required columns for topology metrics (FR-007)
REQUIRED_TOPOLOGY_COLUMNS = {'subject_id', 'clustering_coefficient', 'characteristic_path_length'}


def validate_entrainment_csv(file_path: str) -> Tuple[bool, Optional[str], Optional[pd.DataFrame]]:
    """
    Validates the entrainment metrics CSV file.

    Checks:
    1. File exists and is readable.
    2. Contains required columns: 'subject_id', 'entrainment_metric'.
    3. 'subject_id' is string/object type.
    4. 'entrainment_metric' is numeric.

    Args:
        file_path: Path to the entrainment CSV file.

    Returns:
        Tuple of (is_valid, error_message, dataframe).
        If valid, returns (True, None, df).
        If invalid, returns (False, error_string, None).
    """
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}", None

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return False, f"Failed to read CSV: {str(e)}", None

    # Check for required columns
    missing_cols = REQUIRED_ENTRAINMENT_COLUMNS - set(df.columns)
    if missing_cols:
        return False, f"Missing required columns: {missing_cols}", None

    # Validate data types
    if not pd.api.types.is_string_dtype(df['subject_id']) and not pd.api.types.is_object_dtype(df['subject_id']):
        return False, "Column 'subject_id' must be of string/object type.", None

    if not pd.api.types.is_numeric_dtype(df['entrainment_metric']):
        return False, "Column 'entrainment_metric' must be numeric.", None

    return True, None, df


def validate_topology_columns(file_path: str) -> Tuple[bool, Optional[str], Optional[pd.DataFrame]]:
    """
    Validates the topology metrics CSV file.

    Checks:
    1. File exists and is readable.
    2. Contains required columns: 'subject_id', 'clustering_coefficient', 'characteristic_path_length'.
    3. 'subject_id' is string/object type.
    4. Metric columns are numeric.

    Args:
        file_path: Path to the topology metrics CSV file.

    Returns:
        Tuple of (is_valid, error_message, dataframe).
        If valid, returns (True, None, df).
        If invalid, returns (False, error_string, None).
    """
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}", None

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return False, f"Failed to read CSV: {str(e)}", None

    # Check for required columns
    missing_cols = REQUIRED_TOPOLOGY_COLUMNS - set(df.columns)
    if missing_cols:
        return False, f"Missing required topology columns: {missing_cols}", None

    # Validate data types
    if not pd.api.types.is_string_dtype(df['subject_id']) and not pd.api.types.is_object_dtype(df['subject_id']):
        return False, "Column 'subject_id' must be of string/object type.", None

    metric_cols = ['clustering_coefficient', 'characteristic_path_length']
    for col in metric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            return False, f"Column '{col}' must be numeric.", None

    return True, None, df