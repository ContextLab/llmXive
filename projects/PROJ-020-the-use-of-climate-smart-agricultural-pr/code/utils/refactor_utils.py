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
    Standardize column names: lowercase, replace spaces with underscores, strip special chars.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with standardized column names
    """
    if df is None or df.empty:
        logger.warning("Received empty or None DataFrame in standardize_dataframe_columns")
        return df if df is not None else pd.DataFrame()
        
    # Create mapping of old to new names
    col_mapping = {}
    for col in df.columns:
        new_col = str(col).lower().replace(" ", "_").replace("-", "_").strip("_")
        # Remove special characters except underscores
        new_col = "".join(c if c.isalnum() or c == "_" else "" for c in new_col)
        col_mapping[col] = new_col
        
    # Rename columns
    df_renamed = df.rename(columns=col_mapping)
    logger.info(f"Standardized {len(col_mapping)} column names")
    return df_renamed


def validate_dataframe_schema(df: pd.DataFrame, required_columns: List[str], 
                              optional_columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Validate that a DataFrame contains required columns and optionally check types.
    
    Args:
        df: DataFrame to validate
        required_columns: List of column names that must exist
        optional_columns: List of column names that may exist
        
    Returns:
        Dictionary with validation results: {
            'valid': bool,
            'missing_required': List[str],
            'extra_columns': List[str],
            'column_types': Dict[str, str]
        }
    """
    result = {
        'valid': True,
        'missing_required': [],
        'extra_columns': [],
        'column_types': {}
    }
    
    if df is None or df.empty:
        result['valid'] = False
        result['missing_required'] = required_columns
        return result
        
    current_columns = set(df.columns)
    required_set = set(required_columns)
    
    # Check required columns
    missing = required_set - current_columns
    if missing:
        result['valid'] = False
        result['missing_required'] = list(missing)
        
    # Check optional columns presence
    if optional_columns:
        optional_set = set(optional_columns)
        present_optional = optional_set & current_columns
        result['extra_columns'] = list(present_optional)
        
    # Record column types
    for col in df.columns:
        dtype = str(df[col].dtype)
        result['column_types'][col] = dtype
        
    return result


def safe_column_access(df: pd.DataFrame, column: str, default: Any = None) -> pd.Series:
    """
    Safely access a column, returning default if column doesn't exist.
    
    Args:
        df: Input DataFrame
        column: Column name to access
        default: Default value to return if column missing
        
    Returns:
        Series if column exists, else a Series of default values matching df length
    """
    if df is None or column not in df.columns:
        logger.warning(f"Column '{column}' not found, returning default")
        return pd.Series([default] * len(df)) if df is not None else pd.Series([default])
    return df[column]


def drop_constant_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove columns that have only one unique value (constant columns).
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with constant columns removed
    """
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()
        
    constant_cols = []
    for col in df.columns:
        if df[col].nunique() <= 1:
            constant_cols.append(col)
            
    if constant_cols:
        logger.info(f"Dropping {len(constant_cols)} constant columns: {constant_cols}")
        return df.drop(columns=constant_cols)
    return df


def format_large_number(num: float, precision: int = 2) -> str:
    """
    Format large numbers with SI suffixes (K, M, B, T).
    
    Args:
        num: Number to format
        precision: Decimal places
        
    Returns:
        Formatted string with suffix
    """
    if abs(num) < 1000:
        return f"{num:.{precision}f}"
        
    suffixes = ['', 'K', 'M', 'B', 'T']
    magnitude = 0
    while abs(num) >= 1000 and magnitude < len(suffixes) - 1:
        num /= 1000.0
        magnitude += 1
        
    return f"{num:.{precision}f}{suffixes[magnitude]}"


def ensure_directory_exists(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        Path object for the directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {dir_path}")
    return dir_path


def write_json_with_timestamp(data: Dict[str, Any], output_path: Union[str, Path], 
                             filename_prefix: str = "output") -> Path:
    """
    Write JSON data to a file with a timestamp in the filename.
    
    Args:
        data: Dictionary to serialize as JSON
        output_path: Directory to write file to
        filename_prefix: Prefix for the filename
        
    Returns:
        Path to the created file
    """
    dir_path = ensure_directory_exists(output_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.json"
    file_path = dir_path / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
        
    logger.info(f"Wrote JSON to {file_path}")
    return file_path


def calculate_memory_usage(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate memory usage statistics for a DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with memory usage stats: {
            'total_memory_bytes': int,
            'total_memory_mb': float,
            'per_column_memory': Dict[str, int]
        }
    """
    if df is None or df.empty:
        return {
            'total_memory_bytes': 0,
            'total_memory_mb': 0.0,
            'per_column_memory': {}
        }
        
    per_column = {}
    total_bytes = 0
    
    for col in df.columns:
        col_bytes = df[col].memory_usage(deep=True)
        per_column[col] = col_bytes
        total_bytes += col_bytes
        
    return {
        'total_memory_bytes': total_bytes,
        'total_memory_mb': total_bytes / (1024 * 1024),
        'per_column_memory': per_column
    }


def log_dataframe_info(df: pd.DataFrame, logger_name: str = "dataframe") -> None:
    """
    Log summary information about a DataFrame.
    
    Args:
        df: DataFrame to log info about
        logger_name: Name of the logger to use
    """
    if df is None or df.empty:
        logger.warning("Cannot log info for None or empty DataFrame")
        return
        
    log = logging.getLogger(logger_name)
    log.info(f"DataFrame shape: {df.shape}")
    log.info(f"Memory usage: {calculate_memory_usage(df)['total_memory_mb']:.2f} MB")
    log.info(f"Columns: {list(df.columns)}")
    log.info(f"Null counts:\n{df.isnull().sum()}")
    log.info(f"Data types:\n{df.dtypes}")
