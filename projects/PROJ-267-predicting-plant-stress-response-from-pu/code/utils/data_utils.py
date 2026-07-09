"""
Data loading utilities for CSV and Parquet I/O operations.

This module provides robust functions for reading and writing data
in CSV and Parquet formats, integrated with the project's logging
and configuration infrastructure.
"""
import os
import pandas as pd
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

from .logging_config import get_logger, log_warning
from .config import DATA_RAW_PATH, DATA_PROCESSED_PATH

logger = get_logger(__name__)


def load_csv(
    file_path: Union[str, Path],
    dtype: Optional[Dict[str, Any]] = None,
    usecols: Optional[List[str]] = None,
    na_values: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame with validation.

    Args:
        file_path: Path to the CSV file (absolute or relative to project root).
        dtype: Optional dictionary of column data types.
        usecols: Optional list of columns to load.
        na_values: Optional list of strings to recognize as NA/NaN.

    Returns:
        pd.DataFrame: The loaded data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or cannot be parsed.
    """
    path = Path(file_path)
    if not path.is_absolute():
        # Try relative to project root if not absolute
        if not path.exists():
            path = Path(DATA_RAW_PATH) / path if Path(DATA_RAW_PATH).exists() else path
            if not path.exists():
                path = Path(DATA_PROCESSED_PATH) / path if Path(DATA_PROCESSED_PATH).exists() else path

    if not path.exists():
        logger.error(f"File not found: {path}")
        raise FileNotFoundError(f"Data file not found: {path}")

    logger.info(f"Loading CSV from {path}")

    try:
        df = pd.read_csv(
            path,
            dtype=dtype,
            usecols=usecols,
            na_values=na_values,
            low_memory=False
        )
    except pd.errors.EmptyDataError:
        msg = f"CSV file is empty: {path}"
        logger.error(msg)
        raise ValueError(msg)
    except pd.errors.ParserError as e:
        msg = f"Failed to parse CSV {path}: {e}"
        logger.error(msg)
        raise ValueError(msg)

    if df.empty:
        msg = f"Loaded CSV is empty (0 rows): {path}"
        log_warning(msg)
        # Return empty dataframe with columns if any were specified, else generic
        logger.info(f"Returning empty dataframe for {path}")

    logger.info(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns from {path}")
    return df


def load_parquet(
    file_path: Union[str, Path],
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load a Parquet file into a pandas DataFrame.

    Args:
        file_path: Path to the Parquet file.
        columns: Optional list of columns to load.

    Returns:
        pd.DataFrame: The loaded data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ImportError: If pyarrow or fastparquet is not installed.
    """
    path = Path(file_path)
    if not path.is_absolute():
        if not path.exists():
            path = Path(DATA_RAW_PATH) / path if Path(DATA_RAW_PATH).exists() else path
            if not path.exists():
                path = Path(DATA_PROCESSED_PATH) / path if Path(DATA_PROCESSED_PATH).exists() else path

    if not path.exists():
        logger.error(f"File not found: {path}")
        raise FileNotFoundError(f"Data file not found: {path}")

    logger.info(f"Loading Parquet from {path}")

    try:
        df = pd.read_parquet(path, columns=columns)
    except ImportError as e:
        msg = f"Failed to load Parquet: missing dependency. Ensure 'pyarrow' or 'fastparquet' is installed. Error: {e}"
        logger.error(msg)
        raise ImportError(msg)
    except Exception as e:
        msg = f"Failed to read Parquet file {path}: {e}"
        logger.error(msg)
        raise RuntimeError(msg)

    logger.info(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns from {path}")
    return df


def save_csv(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    index: bool = False
) -> None:
    """
    Save a DataFrame to a CSV file.

    Args:
        df: The DataFrame to save.
        file_path: Destination path (absolute or relative to project root).
        index: Whether to write row indices.
    """
    path = Path(file_path)
    if not path.is_absolute():
        # Default to processed if relative and no specific dir given
        if not path.exists() and not path.parent.exists():
            path = Path(DATA_PROCESSED_PATH) / path

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving CSV to {path}")
    df.to_csv(path, index=index)
    logger.info(f"Successfully saved {len(df)} rows to {path}")


def save_parquet(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    index: bool = False
) -> None:
    """
    Save a DataFrame to a Parquet file.

    Args:
        df: The DataFrame to save.
        file_path: Destination path.
        index: Whether to write row indices.
    """
    path = Path(file_path)
    if not path.is_absolute():
        path = Path(DATA_PROCESSED_PATH) / path

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving Parquet to {path}")
    try:
        df.to_parquet(path, index=index)
    except ImportError as e:
        msg = f"Failed to save Parquet: missing dependency. Ensure 'pyarrow' or 'fastparquet' is installed. Error: {e}"
        logger.error(msg)
        raise ImportError(msg)
    except Exception as e:
        msg = f"Failed to write Parquet file {path}: {e}"
        logger.error(msg)
        raise RuntimeError(msg)

    logger.info(f"Successfully saved {len(df)} rows to {path}")


def detect_file_format(file_path: Union[str, Path]) -> str:
    """
    Detect the file format based on extension.

    Args:
        file_path: Path to the file.

    Returns:
        str: 'csv' or 'parquet'.

    Raises:
        ValueError: If the format is not supported.
    """
    ext = Path(file_path).suffix.lower()
    if ext == '.csv':
        return 'csv'
    elif ext in ('.parquet', '.pq'):
        return 'parquet'
    else:
        msg = f"Unsupported file format: {ext}. Supported: .csv, .parquet"
        logger.error(msg)
        raise ValueError(msg)


def load_data(
    file_path: Union[str, Path],
    **kwargs
) -> pd.DataFrame:
    """
    Generic loader that detects format and delegates to specific loaders.

    Args:
        file_path: Path to the data file.
        **kwargs: Arguments passed to the specific loader (e.g., dtype, columns).

    Returns:
        pd.DataFrame: The loaded data.
    """
    fmt = detect_file_format(file_path)
    if fmt == 'csv':
        return load_csv(file_path, **kwargs)
    elif fmt == 'parquet':
        # Map 'usecols' to 'columns' for parquet if provided
        if 'usecols' in kwargs:
            kwargs['columns'] = kwargs.pop('usecols')
        return load_parquet(file_path, **kwargs)
    raise ValueError(f"Unknown format detected: {fmt}")

def save_data(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    **kwargs
) -> None:
    """
    Generic saver that detects format and delegates to specific savers.

    Args:
        df: DataFrame to save.
        file_path: Destination path.
        **kwargs: Arguments passed to specific saver (e.g., index).
    """
    fmt = detect_file_format(file_path)
    if fmt == 'csv':
        save_csv(df, file_path, **kwargs)
    elif fmt == 'parquet':
        save_parquet(df, file_path, **kwargs)
    else:
        raise ValueError(f"Unknown format: {fmt}")
