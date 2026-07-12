"""
Refactored utility functions for code cleanup and standardization.
Consolidates common patterns used across the data and analysis pipelines.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Union
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


def standardize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names: lowercase, replace spaces with underscores, strip whitespace.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with standardized column names
    """
    df_standardized = df.copy()
    df_standardized.columns = (
        df_standardized.columns
        .str.lower()
        .str.replace(r'\s+', '_', regex=True)
        .str.strip()
    )
    return df_standardized


def validate_dataframe_schema(
    df: pd.DataFrame,
    required_columns: List[str],
    optional_columns: Optional[List[str]] = None,
    strict: bool = False
) -> Dict[str, Any]:
    """
    Validate that a DataFrame contains required columns and optionally report on extra columns.
    
    Args:
        df: Input DataFrame
        required_columns: List of column names that must exist
        optional_columns: List of column names that may exist
        strict: If True, fail if any unexpected columns are present
        
    Returns:
        Dictionary with validation results:
        - 'valid': bool
        - 'missing_columns': List[str]
        - 'unexpected_columns': List[str]
        - 'total_columns': int
    """
    result = {
        'valid': True,
        'missing_columns': [],
        'unexpected_columns': [],
        'total_columns': len(df.columns)
    }
    
    current_columns = set(df.columns)
    required_set = set(required_columns)
    optional_set = set(optional_columns) if optional_columns else set()
    
    # Check for missing required columns
    missing = required_set - current_columns
    if missing:
        result['missing_columns'] = list(missing)
        result['valid'] = False
        logger.warning(f"Missing required columns: {missing}")
    
    # Check for unexpected columns
    if strict:
        expected = required_set | optional_set
        unexpected = current_columns - expected
        if unexpected:
            result['unexpected_columns'] = list(unexpected)
            result['valid'] = False
            logger.warning(f"Unexpected columns in strict mode: {unexpected}")
    
    return result


def safe_column_access(
    df: pd.DataFrame,
    column: str,
    default: Any = None,
    raise_on_missing: bool = False
) -> pd.Series:
    """
    Safely access a column, returning a default value or raising an error if missing.
    
    Args:
        df: Input DataFrame
        column: Column name to access
        default: Default value to return if column is missing
        raise_on_missing: If True, raise KeyError instead of returning default
        
    Returns:
        pd.Series containing the column data
        
    Raises:
        KeyError: If column is missing and raise_on_missing is True
    """
    if column not in df.columns:
        if raise_on_missing:
            raise KeyError(f"Column '{column}' not found in DataFrame")
        logger.warning(f"Column '{column}' not found, returning default")
        return pd.Series([default] * len(df), index=df.index)
    return df[column]


def drop_constant_columns(
    df: pd.DataFrame,
    threshold: float = 0.0
) -> pd.DataFrame:
    """
    Drop columns that have constant values or near-constant values.
    
    Args:
        df: Input DataFrame
        threshold: Fraction of unique values threshold (0.0 = only truly constant)
        
    Returns:
        DataFrame with constant columns removed
    """
    df_clean = df.copy()
    columns_to_drop = []
    
    for col in df_clean.columns:
        if df_clean[col].nunique() == 1:
            columns_to_drop.append(col)
        elif threshold > 0:
            unique_ratio = df_clean[col].nunique() / len(df_clean)
            if unique_ratio <= threshold:
                columns_to_drop.append(col)
    
    if columns_to_drop:
        logger.info(f"Dropping {len(columns_to_drop)} constant/near-constant columns: {columns_to_drop}")
        df_clean = df_clean.drop(columns=columns_to_drop)
    
    return df_clean


def format_large_number(n: Union[int, float]) -> str:
    """
    Format large numbers with appropriate suffixes (K, M, B, T).
    
    Args:
        n: Number to format
        
    Returns:
        Formatted string
    """
    if n >= 1e12:
        return f"{n/1e12:.2f}T"
    elif n >= 1e9:
        return f"{n/1e9:.2f}B"
    elif n >= 1e6:
        return f"{n/1e6:.2f}M"
    elif n >= 1e3:
        return f"{n/1e3:.2f}K"
    else:
        return f"{n:.2f}"


def ensure_directory_exists(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to directory
        
    Returns:
        Path object for the directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {dir_path}")
    return dir_path


def write_json_with_timestamp(
    data: Dict[str, Any],
    output_path: Union[str, Path],
    timestamp_format: str = "%Y%m%d_%H%M%S"
) -> Path:
    """
    Write JSON data to a file with a timestamp in the filename.
    
    Args:
        data: Dictionary to serialize to JSON
        output_path: Base path for output file
        timestamp_format: Format string for timestamp
        
    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    timestamp = datetime.now().strftime(timestamp_format)
    stem = output_path.stem
    suffix = output_path.suffix
    
    new_filename = f"{stem}_{timestamp}{suffix}"
    final_path = output_path.parent / new_filename
    
    with open(final_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Wrote JSON to {final_path}")
    return final_path


def calculate_memory_usage(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate memory usage statistics for a DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with memory usage stats in MB
    """
    total_memory = df.memory_usage(deep=True).sum() / (1024 * 1024)
    per_column = {col: mem / (1024 * 1024) for col, mem in df.memory_usage(deep=True).items()}
    
    return {
        'total_mb': total_memory,
        'per_column_mb': per_column,
        'num_rows': len(df),
        'num_columns': len(df.columns)
    }


def log_dataframe_info(df: pd.DataFrame, logger_name: str = "data_utils") -> None:
    """
    Log comprehensive information about a DataFrame.
    
    Args:
        df: Input DataFrame
        logger_name: Name of the logger to use
    """
    log = logging.getLogger(logger_name)
    memory_info = calculate_memory_usage(df)
    
    log.info(f"DataFrame shape: {df.shape}")
    log.info(f"Total memory usage: {memory_info['total_mb']:.2f} MB")
    log.info(f"Number of rows: {memory_info['num_rows']}")
    log.info(f"Number of columns: {memory_info['num_columns']}")
    
    log.debug("Column memory usage:")
    for col, mem in memory_info['per_column_mb'].items():
        log.debug(f"  {col}: {mem:.4f} MB")
    
    log.debug("Column dtypes:")
    for col, dtype in df.dtypes.items():
        log.debug(f"  {col}: {dtype}")
    
    log.debug("Missing values per column:")
    missing_counts = df.isnull().sum()
    for col, count in missing_counts.items():
        if count > 0:
            log.debug(f"  {col}: {count} ({100*count/len(df):.2f}%)")
