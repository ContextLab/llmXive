"""
Data loading and saving utilities for the DSSC project.
Provides CSV I/O functions using pandas.
"""
import pandas as pd
from pathlib import Path
from typing import Union

from utils.logger import setup_logger

logger = setup_logger(__name__)


def load_csv(path: str) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.

    Args:
        path: Path to the CSV file (relative or absolute).

    Returns:
        pd.DataFrame: The loaded data.

    Raises:
        FileNotFoundError: If the file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
        Exception: For other I/O errors.
    """
    file_path = Path(path)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        logger.info(f"Loading CSV from {file_path}")
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
        return df
    except pd.errors.EmptyDataError:
        logger.error(f"File is empty: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading CSV {file_path}: {e}")
        raise


def save_csv(df: pd.DataFrame, path: str) -> None:
    """
    Save a pandas DataFrame to a CSV file.

    Args:
        df: The DataFrame to save.
        path: Path to the output CSV file.

    Raises:
        Exception: If the save operation fails.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Saving DataFrame to {file_path} ({len(df)} rows)")
        df.to_csv(file_path, index=False)
        logger.info("Save successful")
    except Exception as e:
        logger.error(f"Error saving CSV {file_path}: {e}")
        raise
