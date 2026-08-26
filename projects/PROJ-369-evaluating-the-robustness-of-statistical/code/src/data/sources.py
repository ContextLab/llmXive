"""
Centralized data source definitions for the robustness evaluation pipeline.

This module serves as the SINGLE source of truth for all dataset URLs and
metadata to prevent URL drift and ensure reproducibility (Spec FR-001,
Constitution Principle II).
"""

from typing import Dict, Any, List

# Dataset source definitions
# Keys are internal dataset names used throughout the pipeline
DATA_SOURCES: Dict[str, Dict[str, Any]] = {
    "NOAA_GSWD": {
        "name": "NOAA Global Summary of the Day",
        "url": "https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/1950-2022/USW00014833.csv",
        "expected_format": "csv",
        "checksum_url": None,  # NOAA does not provide direct checksums for these files
        "description": "Daily weather data for New York Central Park (USW00014833)",
        "columns": ["Date", "TMAX", "TMIN", "PRCP"],
        "date_column": "Date",
        "value_columns": ["TMAX", "TMIN", "PRCP"]
    },
    "NOAA_PHX": {
        "name": "NOAA Global Summary of the Day - Phoenix",
        "url": "https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/1950-2022/USW00014895.csv",
        "expected_format": "csv",
        "checksum_url": None,
        "description": "Daily weather data for Phoenix Sky Harbor (USW00014895)",
        "columns": ["Date", "TMAX", "TMIN", "PRCP"],
        "date_column": "Date",
        "value_columns": ["TMAX", "TMIN", "PRCP"]
    },
    "UK_GRID": {
        "name": "UK National Grid Electricity Load",
        "url": "https://www.nationalgrideso.com/document/174276/download",
        "expected_format": "csv",
        "checksum_url": None,
        "description": "Half-hourly electricity load data for Great Britain",
        "columns": ["DateTime", "Load"],
        "date_column": "DateTime",
        "value_columns": ["Load"]
    },
    "YF_AAPL": {
        "name": "Apple Inc. Stock Prices",
        "url": None,  # Downloaded via yfinance package
        "expected_format": "csv",
        "checksum_url": None,
        "description": "Daily adjusted close prices for Apple Inc.",
        "ticker": "AAPL",
        "value_columns": ["Adj Close"]
    },
    "YF_SPY": {
        "name": "SPDR S&P 500 ETF Trust",
        "url": None,  # Downloaded via yfinance package
        "expected_format": "csv",
        "checksum_url": None,
        "description": "Daily adjusted close prices for SPY ETF",
        "ticker": "SPY",
        "value_columns": ["Adj Close"]
    }
}

def get_source_info(dataset_name: str) -> Dict[str, Any]:
    """
    Retrieve information for a specific dataset source.
    
    Args:
        dataset_name: The internal name of the dataset (e.g., "NOAA_GSWD")
        
    Returns:
        Dictionary containing source metadata
        
    Raises:
        KeyError: If dataset_name is not found in DATA_SOURCES
    """
    if dataset_name not in DATA_SOURCES:
        raise KeyError(f"Dataset '{dataset_name}' not found in DATA_SOURCES. "
                     f"Available: {list(DATA_SOURCES.keys())}")
    return DATA_SOURCES[dataset_name]

def get_all_source_names() -> List[str]:
    """
    Get a list of all available dataset names.
    
    Returns:
        List of dataset names (keys of DATA_SOURCES)
    """
    return list(DATA_SOURCES.keys())

def get_yfinance_symbols() -> List[str]:
    """
    Get list of tickers that should be downloaded via yfinance.
    
    Returns:
        List of ticker symbols
    """
    return [
        source["ticker"] 
        for source in DATA_SOURCES.values() 
        if source.get("url") is None and "ticker" in source
    ]

def get_direct_download_urls() -> Dict[str, str]:
    """
    Get mapping of dataset names to direct download URLs.
    
    Returns:
        Dictionary of dataset_name -> URL for datasets with direct URLs
    """
    return {
        name: source["url"]
        for name, source in DATA_SOURCES.items()
        if source.get("url") is not None
    }

def validate_source_exists(dataset_name: str) -> bool:
    """
    Check if a dataset source is defined.
    
    Args:
        dataset_name: The internal name of the dataset
        
    Returns:
        True if the dataset is defined, False otherwise
    """
    return dataset_name in DATA_SOURCES