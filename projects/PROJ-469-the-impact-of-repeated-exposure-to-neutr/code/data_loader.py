"""
Data loading module for the Political IAT analysis.

This module handles the loading of raw CSV data from the data/raw directory,
validates the existence of required data, maps raw columns to analysis variables
using the project codebook, and raises appropriate errors if data is missing
or invalid.
"""

import os
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List

# Import shared configuration utilities
from config import ensure_dirs
from logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

# Codebook mapping raw column names to standard analysis variable names
# This mapping is derived from the Project Implicit data dictionary.
# If a raw column name changes, update this mapping here.
CODEBOOK_MAPPING: Dict[str, str] = {
    # IAT Score (D-score algorithm)
    'D_Score': 'IAT_D_score',
    'd_score': 'IAT_D_score',
    'd_score_600': 'IAT_D_score',
    
    # Political Ideology (Self-reported, typically 1-7 scale)
    'political_ideology': 'political_ideology',
    'ideology': 'political_ideology',
    'pol_ideology': 'political_ideology',
    'self_reported_ideology': 'political_ideology',
    
    # News Exposure Frequency
    'news_exposure_freq': 'news_exposure_freq',
    'news_frequency': 'news_exposure_freq',
    'freq_news': 'news_exposure_freq',
    'political_news_exposure': 'news_exposure_freq',
}

# Standard analysis columns required for the primary model
REQUIRED_STANDARD_COLUMNS: List[str] = [
    'IAT_D_score',
    'political_ideology',
    'news_exposure_freq'
]

def get_data_path() -> Path:
    """
    Get the path to the raw data directory.
    
    Returns:
        Path: The absolute path to data/raw/
    """
    return Path("data/raw")


def validate_data_directory() -> bool:
    """
    Validate that the raw data directory exists.
    
    Returns:
        bool: True if directory exists, False otherwise.
    """
    data_dir = get_data_path()
    return data_dir.exists() and data_dir.is_dir()


def load_csv(filename: str, base_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Load a CSV file from the raw data directory.
    
    Args:
        filename: Name of the CSV file to load.
        base_dir: Optional base directory. Defaults to data/raw/.
    
    Returns:
        pd.DataFrame: The loaded DataFrame.
    
    Raises:
        ValueError: If the data directory does not exist.
        FileNotFoundError: If the specified file is not found.
    """
    if base_dir is None:
        base_dir = get_data_path()
    
    # Ensure the data directory exists
    if not validate_data_directory():
        raise ValueError(
            f"Data directory '{base_dir}' does not exist. "
            "Please ensure data has been fetched to data/raw/."
        )
    
    file_path = base_dir / filename
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"Data file '{filename}' not found in '{base_dir}'. "
            "Run the data fetcher script to download the dataset."
        )
    
    return pd.read_csv(file_path)


def load_project_implicit_data(
    filename: str = "political_iat_data.csv",
    base_dir: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load the Project Implicit dataset and map columns to standard names.
    
    This function loads the raw CSV, applies the codebook mapping to rename
    columns to standard analysis variable names (IAT_D_score, political_ideology,
    news_exposure_freq), and validates that all required columns are present.
    
    Args:
        filename: Name of the CSV file (default: 'political_iat_data.csv').
        base_dir: Optional base directory for data.
    
    Returns:
        pd.DataFrame: The loaded and mapped Project Implicit dataset.
    
    Raises:
        ValueError: If the data directory does not exist or required columns
                   are missing after mapping.
        FileNotFoundError: If the dataset file is not found.
    """
    logger.info(f"Loading Project Implicit data from {filename}")
    
    # Load raw data
    df_raw = load_csv(filename, base_dir)
    
    # Apply codebook mapping
    df_mapped = df_raw.rename(columns=CODEBOOK_MAPPING)
    
    # Log mapping results
    original_cols = set(df_raw.columns)
    mapped_cols = set(df_mapped.columns)
    changed_cols = original_cols.symmetric_difference(mapped_cols)
    if changed_cols:
        logger.debug(f"Column mapping changed: {changed_cols}")
    
    # Validate required columns
    check_required_columns(df_mapped, REQUIRED_STANDARD_COLUMNS)
    
    logger.info(
        f"Successfully loaded data with {len(df_mapped)} rows and "
        f"columns: {list(df_mapped.columns)}"
    )
    
    return df_mapped


def check_required_columns(df: pd.DataFrame, required_columns: list) -> None:
    """
    Validate that a DataFrame contains all required columns.
    
    Args:
        df: The DataFrame to validate.
        required_columns: List of column names that must be present.
    
    Raises:
        ValueError: If any required columns are missing.
    """
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns in dataset: {missing}. "
            f"Available columns: {list(df.columns)}. "
            "Ensure the codebook mapping in data_loader.py is up-to-date."
        )