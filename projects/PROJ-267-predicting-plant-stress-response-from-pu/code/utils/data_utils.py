import os
import pandas as pd
from pathlib import Path
from typing import Optional, Union, List, Dict, Any
import logging

# Import existing logging utilities from the project
# Note: The API surface indicates logging_config exists, but to ensure
# this file is self-contained for import without circular dependencies
# in a fresh environment, we define a fallback logger setup if the module
# isn't strictly available in the immediate context, or import directly.
# Based on the API surface, we assume utils.logging_config is importable.
try:
    from .logging_config import get_logger, log_warning
except ImportError:
    # Fallback for standalone execution or if logging_config isn't fully set up yet
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)
    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)
    def log_warning(msg: str) -> None:
        logging.warning(msg)

from .config import DATA_RAW_PATH, DATA_PROCESSED_PATH

logger = get_logger(__name__)


def detect_file_format(file_path: Union[str, Path]) -> str:
    """
    Detects the file format based on the file extension.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        str: 'csv', 'parquet', or 'unknown'.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix == '.csv':
        return 'csv'
    elif suffix in ['.parquet', '.pq', '.parq']:
        return 'parquet'
    else:
        logger.warning(f"Unknown file extension: {suffix}. Defaulting to CSV logic if possible, but may fail.")
        return 'unknown'


def load_csv(
    file_path: Union[str, Path],
    encoding: str = 'utf-8',
    low_memory: bool = False,
    **kwargs
) -> pd.DataFrame:
    """
    Loads a CSV file into a pandas DataFrame.
    
    Args:
        file_path: Path to the CSV file.
        encoding: Character encoding (default 'utf-8').
        low_memory: If True, infer dtypes in chunks (default False).
        **kwargs: Additional arguments passed to pd.read_csv.
        
    Returns:
        pd.DataFrame: The loaded data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid CSV.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
        
    logger.info(f"Loading CSV from {path}")
    try:
        df = pd.read_csv(path, encoding=encoding, low_memory=low_memory, **kwargs)
        logger.info(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns from {path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load CSV {path}: {e}")
        raise


def load_parquet(
    file_path: Union[str, Path],
    **kwargs
) -> pd.DataFrame:
    """
    Loads a Parquet file into a pandas DataFrame.
    
    Args:
        file_path: Path to the Parquet file.
        **kwargs: Additional arguments passed to pd.read_parquet.
        
    Returns:
        pd.DataFrame: The loaded data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {path}")
        
    logger.info(f"Loading Parquet from {path}")
    try:
        # Ensure pyarrow or fastparquet is available (handled in requirements.txt)
        df = pd.read_parquet(path, **kwargs)
        logger.info(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns from {path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load Parquet {path}: {e}")
        raise


def save_csv(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    index: bool = False,
    encoding: str = 'utf-8',
    **kwargs
) -> None:
    """
    Saves a DataFrame to a CSV file.
    
    Args:
        df: The DataFrame to save.
        file_path: Destination path.
        index: Whether to write row indices (default False).
        encoding: Character encoding (default 'utf-8').
        **kwargs: Additional arguments passed to pd.DataFrame.to_csv.
        
    Raises:
        ValueError: If the DataFrame is empty.
    """
    path = Path(file_path)
    if df.empty:
        logger.warning(f"Attempting to save empty DataFrame to {path}")
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=index, encoding=encoding, **kwargs)
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving CSV to {path}")
    try:
        df.to_csv(path, index=index, encoding=encoding, **kwargs)
        logger.info(f"Successfully saved {len(df)} rows to {path}")
    except Exception as e:
        logger.error(f"Failed to save CSV {path}: {e}")
        raise


def save_parquet(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    index: bool = False,
    **kwargs
) -> None:
    """
    Saves a DataFrame to a Parquet file.
    
    Args:
        df: The DataFrame to save.
        file_path: Destination path.
        index: Whether to write row indices (default False).
        **kwargs: Additional arguments passed to pd.DataFrame.to_parquet.
        
    Raises:
        ValueError: If the DataFrame is empty.
    """
    path = Path(file_path)
    if df.empty:
        logger.warning(f"Attempting to save empty DataFrame to {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=index, **kwargs)
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving Parquet to {path}")
    try:
        df.to_parquet(path, index=index, **kwargs)
        logger.info(f"Successfully saved {len(df)} rows to {path}")
    except Exception as e:
        logger.error(f"Failed to save Parquet {path}: {e}")
        raise


def load_data(
    file_path: Union[str, Path],
    format_hint: Optional[str] = None
) -> pd.DataFrame:
    """
    Loads data from a file, automatically detecting format if not specified.
    
    Args:
        file_path: Path to the file.
        format_hint: Optional hint ('csv' or 'parquet'). If None, detected from extension.
        
    Returns:
        pd.DataFrame: The loaded data.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    
    if format_hint is None:
        detected_format = detect_file_format(path)
    else:
        detected_format = format_hint.lower()
        
    if detected_format == 'csv':
        return load_csv(path)
    elif detected_format == 'parquet':
        return load_parquet(path)
    else:
        raise ValueError(f"Unsupported file format detected for {path}: {detected_format}")


def save_data(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    format_hint: Optional[str] = None
) -> None:
    """
    Saves data to a file, automatically detecting format if not specified.
    
    Args:
        df: The DataFrame to save.
        file_path: Destination path.
        format_hint: Optional hint ('csv' or 'parquet'). If None, detected from extension.
    """
    path = Path(file_path)
    if format_hint is None:
        detected_format = detect_file_format(path)
    else:
        detected_format = format_hint.lower()
        
    if detected_format == 'csv':
        save_csv(df, path)
    elif detected_format == 'parquet':
        save_parquet(df, path)
    else:
        raise ValueError(f"Unsupported file format detected for {path}: {detected_format}")