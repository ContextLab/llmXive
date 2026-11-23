"""
Common I/O utilities for the llmXive plant stress response pipeline.

This module centralizes file reading, writing, and format detection logic
to ensure consistency across the project and reduce code duplication.
"""

import os
import json
import logging
from pathlib import Path
from typing import Union, Optional, Dict, Any, List

import pandas as pd

from .config import get_project_root, get_data_path, get_results_path, get_log_path
from .logging_config import get_logger, log_warning

logger = get_logger(__name__)


def detect_file_format(file_path: Union[str, Path]) -> str:
    """
    Detect the file format based on the extension.

    Args:
        file_path: Path to the file.

    Returns:
        str: The format string ('csv', 'parquet', 'json', 'txt', or 'unknown').
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    format_map = {
        '.csv': 'csv',
        '.parquet': 'parquet',
        '.json': 'json',
        '.txt': 'txt',
        '.tsv': 'tsv'
    }

    return format_map.get(suffix, 'unknown')


def load_csv(
    file_path: Union[str, Path],
    index_col: Optional[Union[str, int]] = None,
    **kwargs
) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.

    Args:
        file_path: Path to the CSV file.
        index_col: Column to use as the row labels.
        **kwargs: Additional arguments passed to pd.read_csv.

    Returns:
        pd.DataFrame: The loaded data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is not CSV.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if detect_file_format(path) != 'csv':
        log_warning(f"File {path} does not have a .csv extension. Attempting to load anyway.")

    logger.debug(f"Loading CSV from {path}")
    return pd.read_csv(path, index_col=index_col, **kwargs)


def load_parquet(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    Load a Parquet file into a pandas DataFrame.

    Args:
        file_path: Path to the Parquet file.
        **kwargs: Additional arguments passed to pd.read_parquet.

    Returns:
        pd.DataFrame: The loaded data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is not Parquet.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if detect_file_format(path) != 'parquet':
        log_warning(f"File {path} does not have a .parquet extension. Attempting to load anyway.")

    logger.debug(f"Loading Parquet from {path}")
    return pd.read_parquet(path, **kwargs)


def load_json(file_path: Union[str, Path], **kwargs) -> Any:
    """
    Load a JSON file.

    Args:
        file_path: Path to the JSON file.
        **kwargs: Additional arguments passed to json.load.

    Returns:
        Any: The parsed JSON content.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    logger.debug(f"Loading JSON from {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f, **kwargs)


def save_csv(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    index: bool = False,
    **kwargs
) -> None:
    """
    Save a DataFrame to a CSV file.

    Args:
        df: The DataFrame to save.
        file_path: Path to the output file.
        index: Whether to write row names.
        **kwargs: Additional arguments passed to df.to_csv.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Saving CSV to {path}")
    df.to_csv(path, index=index, **kwargs)


def save_parquet(df: pd.DataFrame, file_path: Union[str, Path], **kwargs) -> None:
    """
    Save a DataFrame to a Parquet file.

    Args:
        df: The DataFrame to save.
        file_path: Path to the output file.
        **kwargs: Additional arguments passed to df.to_parquet.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Saving Parquet to {path}")
    df.to_parquet(path, **kwargs)


def save_json(data: Any, file_path: Union[str, Path], indent: int = 2, **kwargs) -> None:
    """
    Save data to a JSON file.

    Args:
        data: The data to save (must be JSON serializable).
        file_path: Path to the output file.
        indent: Indentation level for pretty printing.
        **kwargs: Additional arguments passed to json.dump.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Saving JSON to {path}")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, **kwargs)


def load_data(
    file_path: Union[str, Path],
    **kwargs
) -> Union[pd.DataFrame, Any]:
    """
    Load data from a file, automatically detecting the format.

    Args:
        file_path: Path to the file.
        **kwargs: Additional arguments passed to the specific loader.

    Returns:
        Union[pd.DataFrame, Any]: The loaded data.

    Raises:
        ValueError: If the file format is unsupported.
    """
    fmt = detect_file_format(file_path)

    if fmt == 'csv':
        return load_csv(file_path, **kwargs)
    elif fmt == 'parquet':
        return load_parquet(file_path, **kwargs)
    elif fmt == 'json':
        return load_json(file_path, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {fmt} for file {file_path}")


def save_data(
    data: Union[pd.DataFrame, Any],
    file_path: Union[str, Path],
    **kwargs
) -> None:
    """
    Save data to a file, automatically detecting the format from the extension.

    Args:
        data: The data to save.
        file_path: Path to the output file.
        **kwargs: Additional arguments passed to the specific saver.
    """
    fmt = detect_file_format(file_path)

    if fmt == 'csv':
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Expected pandas DataFrame for CSV output.")
        save_csv(data, file_path, **kwargs)
    elif fmt == 'parquet':
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Expected pandas DataFrame for Parquet output.")
        save_parquet(data, file_path, **kwargs)
    elif fmt == 'json':
        save_json(data, file_path, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {fmt} for file {file_path}")


def ensure_directory(dir_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        dir_path: Path to the directory.

    Returns:
        Path: The path to the directory.
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get the size of a file in bytes.

    Args:
        file_path: Path to the file.

    Returns:
        int: Size in bytes.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.stat().st_size