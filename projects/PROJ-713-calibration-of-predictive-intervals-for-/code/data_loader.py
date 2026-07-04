import os
import hashlib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, List, Dict, Optional
import logging
from urllib.request import urlretrieve
from config import (
    PROJECT_ROOT, DATA_RAW_DIR, DATA_PROCESSED_DIR, 
    M4_URL, UCI_ELECTRICITY_URL, M4_CHECKSUM, UCI_ELECTRICITY_CHECKSUM, TRAIN_SPLIT_RATIO
)
from utils.logger import get_logger
from utils.exceptions import DataFetchError, DataValidationError

logger = get_logger(__name__)

def _calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_data(url: str, filename: str, expected_checksum: Optional[str] = None) -> Path:
    """Fetch data from a URL and save it to the raw data directory.
    
    Args:
        url: URL to fetch data from.
        filename: Name to save the file as.
        expected_checksum: Optional SHA256 checksum to verify against.
        
    Returns:
        Path to the downloaded file.
        
    Raises:
        DataFetchError: If download fails or checksum mismatch.
    """
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    file_path = DATA_RAW_DIR / filename
    
    if file_path.exists():
        logger.info(f"File {filename} already exists. Skipping download.")
    else:
        logger.info(f"Downloading {filename} from {url}...")
        try:
            urlretrieve(url, file_path)
        except Exception as e:
            raise DataFetchError(f"Failed to download {filename}: {e}")
        
        if expected_checksum:
            actual_checksum = _calculate_file_checksum(file_path)
            if actual_checksum != expected_checksum:
                raise DataFetchError(
                    f"Checksum mismatch for {filename}. Expected: {expected_checksum}, Got: {actual_checksum}"
                )
            logger.info(f"Checksum verified for {filename}.")
    
    return file_path

def load_m4_hourly() -> pd.DataFrame:
    """Load M4 Hourly dataset.
    
    Returns:
        DataFrame with M4 Hourly data.
    """
    file_path = fetch_data(M4_URL, "m4_hourly.csv", M4_CHECKSUM)
    # M4 Hourly data typically has 'V1' as series ID and columns as time steps
    # Adjust parsing based on actual M4 format if needed
    df = pd.read_csv(file_path)
    logger.info(f"Loaded M4 Hourly dataset with shape {df.shape}")
    return df

def load_uci_electricity() -> pd.DataFrame:
    """Load UCI Electricity Load Diagrams dataset.
    
    Returns:
        DataFrame with UCI Electricity data.
    """
    file_path = fetch_data(
        UCI_ELECTRICITY_URL, 
        "LD2011_2014.txt", 
        UCI_ELECTRICITY_CHECKSUM
    )
    # UCI Electricity data is semicolon-separated with datetime index
    df = pd.read_csv(
        file_path, 
        sep=';', 
        index_col=0, 
        parse_dates=True, 
        decimal=','
    )
    logger.info(f"Loaded UCI Electricity dataset with shape {df.shape}")
    return df

def split_series(series: pd.Series, train_ratio: float = TRAIN_SPLIT_RATIO) -> Tuple[pd.Series, pd.Series]:
    """Split a time series into training and testing sets.
    
    Args:
        series: Input time series.
        train_ratio: Ratio of data to use for training (default 0.80).
        
    Returns:
        Tuple of (train_series, test_series).
        
    Raises:
        DataValidationError: If series is too short to split.
    """
    if len(series) < 10:
        raise DataValidationError("Series too short to split into train/test sets.")
    
    split_idx = int(len(series) * train_ratio)
    train = series[:split_idx]
    test = series[split_idx:]
    
    logger.debug(f"Split series: train={len(train)}, test={len(test)}")
    return train, test

def standardize(series: pd.Series) -> Tuple[pd.Series, float, float]:
    """Standardize a time series to zero mean and unit variance.
    
    Args:
        series: Input time series.
        
    Returns:
        Tuple of (standardized_series, mean, std).
    """
    mean = series.mean()
    std = series.std()
    
    if std == 0:
        logger.warning("Standard deviation is zero. Returning original series.")
        return series, mean, std
    
    standardized = (series - mean) / std
    return standardized, mean, std
