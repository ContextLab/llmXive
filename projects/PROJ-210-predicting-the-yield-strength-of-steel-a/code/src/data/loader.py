"""
Data loading utilities for CSV and Parquet formats with memory monitoring.

This module provides functions to load data efficiently, monitor memory usage,
and optimize DataFrame memory footprint.
"""
import os
import gc
import psutil
import traceback
from typing import Optional, Dict, Any, Union, Literal
import pandas as pd
import numpy as np

# Import config for path constants
try:
    from src.utils.config import PROJECT_ROOT, DATA_RAW_DIR, DATA_PROCESSED_DIR
except ImportError:
    # Fallback if config is not yet available during initial setup
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    DATA_RAW_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
    DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')


def get_memory_usage_mb() -> float:
    """
    Get current memory usage of the Python process in megabytes.
    
    Returns:
        float: Memory usage in MB
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)


def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage by downcasting numeric types and converting 
    object columns to categorical where appropriate.
    
    Args:
        df: Input DataFrame to optimize
        
    Returns:
        pd.DataFrame: Memory-optimized DataFrame
    """
    if df is None or df.empty:
        return df
        
    initial_memory = df.memory_usage(deep=True).sum()
    
    # Convert numeric columns to smallest possible type
    for col in df.select_dtypes(include=['int64', 'float64']).columns:
        col_min = df[col].min()
        col_max = df[col].max()
        
        if pd.api.types.is_integer_dtype(df[col]):
            if col_min > np.iinfo(np.int8).min and col_max < np.iinfo(np.int8).max:
                df[col] = df[col].astype(np.int8)
            elif col_min > np.iinfo(np.int16).min and col_max < np.iinfo(np.int16).max:
                df[col] = df[col].astype(np.int16)
            elif col_min > np.iinfo(np.int32).min and col_max < np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
        elif pd.api.types.is_float_dtype(df[col]):
            if col_min > np.finfo(np.float32).min and col_max < np.finfo(np.float32).max:
                df[col] = df[col].astype(np.float32)
    
    # Convert object columns to categorical if unique values are low
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() / len(df) < 0.5:  # Less than 50% unique values
            df[col] = df[col].astype('category')
    
    gc.collect()
    
    return df


def load_csv(
    filepath: str,
    optimize_memory: bool = True,
    expected_columns: Optional[list] = None
) -> pd.DataFrame:
    """
    Load a CSV file with optional memory optimization and column validation.
    
    Args:
        filepath: Path to the CSV file (absolute or relative to PROJECT_ROOT)
        optimize_memory: Whether to optimize DataFrame memory after loading
        expected_columns: Optional list of expected column names for validation
        
    Returns:
        pd.DataFrame: Loaded and optionally optimized DataFrame
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If expected columns don't match
    """
    # Handle relative paths
    if not os.path.isabs(filepath):
        # Try relative to PROJECT_ROOT first
        full_path = os.path.join(PROJECT_ROOT, filepath)
        if not os.path.exists(full_path):
            # Try relative to current working directory
            full_path = filepath
    else:
        full_path = filepath
        
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"CSV file not found: {full_path}")
    
    logging = __import__('logging')
    logger = logging.getLogger(__name__)
    logger.info(f"Loading CSV from: {full_path}")
    
    mem_before = get_memory_usage_mb()
    df = pd.read_csv(full_path)
    mem_after = get_memory_usage_mb()
    
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns. "
               f"Memory increase: {mem_after - mem_before:.2f} MB")
    
    if expected_columns is not None:
        missing = set(expected_columns) - set(df.columns)
        if missing:
            raise ValueError(f"Missing expected columns: {missing}")
    
    if optimize_memory:
        df = optimize_dataframe_memory(df)
        logger.info(f"Memory optimized. Final size: {df.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")
    
    return df


def load_parquet(
    filepath: str,
    optimize_memory: bool = True,
    expected_columns: Optional[list] = None
) -> pd.DataFrame:
    """
    Load a Parquet file with optional memory optimization and column validation.
    
    Args:
        filepath: Path to the Parquet file (absolute or relative to PROJECT_ROOT)
        optimize_memory: Whether to optimize DataFrame memory after loading
        expected_columns: Optional list of expected column names for validation
        
    Returns:
        pd.DataFrame: Loaded and optionally optimized DataFrame
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If expected columns don't match
    """
    # Handle relative paths
    if not os.path.isabs(filepath):
        full_path = os.path.join(PROJECT_ROOT, filepath)
        if not os.path.exists(full_path):
            full_path = filepath
    else:
        full_path = filepath
        
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Parquet file not found: {full_path}")
    
    logging = __import__('logging')
    logger = logging.getLogger(__name__)
    logger.info(f"Loading Parquet from: {full_path}")
    
    mem_before = get_memory_usage_mb()
    df = pd.read_parquet(full_path)
    mem_after = get_memory_usage_mb()
    
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns. "
               f"Memory increase: {mem_after - mem_before:.2f} MB")
    
    if expected_columns is not None:
        missing = set(expected_columns) - set(df.columns)
        if missing:
            raise ValueError(f"Missing expected columns: {missing}")
    
    if optimize_memory:
        df = optimize_dataframe_memory(df)
        logger.info(f"Memory optimized. Final size: {df.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")
    
    return df


def load_data(
    filepath: str,
    file_type: Optional[str] = None,
    optimize_memory: bool = True,
    expected_columns: Optional[list] = None
) -> pd.DataFrame:
    """
    Load data from CSV or Parquet file, auto-detecting format if not specified.
    
    Args:
        filepath: Path to the data file
        file_type: Optional explicit file type ('csv' or 'parquet')
        optimize_memory: Whether to optimize DataFrame memory after loading
        expected_columns: Optional list of expected column names for validation
        
    Returns:
        pd.DataFrame: Loaded and optionally optimized DataFrame
        
    Raises:
        ValueError: If file type cannot be determined or is unsupported
        FileNotFoundError: If the file does not exist
    """
    if file_type is None:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.csv':
            file_type = 'csv'
        elif ext in ['.parquet', '.pq']:
            file_type = 'parquet'
        else:
            raise ValueError(f"Unsupported file extension: {ext}. Use 'csv' or 'parquet'.")
    
    if file_type == 'csv':
        return load_csv(filepath, optimize_memory, expected_columns)
    elif file_type == 'parquet':
        return load_parquet(filepath, optimize_memory, expected_columns)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def get_memory_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a detailed memory profile of a DataFrame.
    
    Args:
        df: DataFrame to profile
        
    Returns:
        dict: Memory profile including total memory, per-column memory, and dtypes
    """
    if df is None or df.empty:
        return {
            'total_memory_mb': 0.0,
            'n_rows': 0,
            'n_columns': 0,
            'columns': {}
        }
    
    mem_usage = df.memory_usage(deep=True)
    total_memory = mem_usage.sum()
    
    profile = {
        'total_memory_mb': total_memory / (1024 * 1024),
        'n_rows': len(df),
        'n_columns': len(df.columns),
        'columns': {}
    }
    
    for col in df.columns:
        col_mem = mem_usage[col]
        profile['columns'][col] = {
            'memory_mb': col_mem / (1024 * 1024),
            'dtype': str(df[col].dtype),
            'n_unique': df[col].nunique(),
            'n_null': df[col].isnull().sum()
        }
    
    return profile


def print_memory_profile(df: pd.DataFrame, title: str = "Memory Profile") -> None:
    """
    Print a formatted memory profile of a DataFrame to stdout.
    
    Args:
        df: DataFrame to profile
        title: Title for the profile output
    """
    profile = get_memory_profile(df)
    
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Total Memory: {profile['total_memory_mb']:.2f} MB")
    print(f"Rows: {profile['n_rows']:,}, Columns: {profile['n_columns']}")
    print(f"{'-'*60}")
    print(f"{'Column':<30} {'Size (MB)':<12} {'Dtype':<15} {'Unique':<10} {'Nulls':<10}")
    print(f"{'-'*60}")
    
    for col, stats in profile['columns'].items():
        print(f"{col:<30} {stats['memory_mb']:<12.4f} {stats['dtype']:<15} "
             f"{stats['n_unique']:<10} {stats['n_null']:<10}")
    
    print(f"{'='*60}\n")


def validate_data_load(
    df: pd.DataFrame,
    expected_rows: Optional[int] = None,
    expected_columns: Optional[list] = None,
    required_columns: Optional[list] = None,
    max_null_ratio: float = 0.0
) -> Dict[str, Any]:
    """
    Validate a loaded DataFrame against various criteria.
    
    Args:
        df: DataFrame to validate
        expected_rows: Expected number of rows (optional)
        expected_columns: Expected list of column names (optional)
        required_columns: List of columns that must be present (optional)
        max_null_ratio: Maximum allowed null ratio per column (default: 0.0)
        
    Returns:
        dict: Validation results with success flag and details
    """
    results = {
        'success': True,
        'issues': [],
        'warnings': [],
        'memory_mb': df.memory_usage(deep=True).sum() / (1024 * 1024) if df is not None else 0
    }
    
    if df is None or df.empty:
        results['success'] = False
        results['issues'].append("DataFrame is empty or None")
        return results
    
    # Check expected rows
    if expected_rows is not None and len(df) != expected_rows:
        results['warnings'].append(f"Row count mismatch: expected {expected_rows}, got {len(df)}")
    
    # Check expected columns
    if expected_columns is not None:
        missing = set(expected_columns) - set(df.columns)
        if missing:
            results['issues'].append(f"Missing expected columns: {missing}")
            results['success'] = False
    
    # Check required columns
    if required_columns is not None:
        missing = set(required_columns) - set(df.columns)
        if missing:
            results['issues'].append(f"Missing required columns: {missing}")
            results['success'] = False
    
    # Check null ratios
    if max_null_ratio > 0:
        for col in df.columns:
            null_ratio = df[col].isnull().sum() / len(df)
            if null_ratio > max_null_ratio:
                results['warnings'].append(
                    f"Column '{col}' has null ratio {null_ratio:.2%} > {max_null_ratio:.2%}"
                )
    
    return results