"""
Real dataset loader for the Social Validation study.

Attempts to fetch real data from verified sources.
Raises DataLoadError if fetching fails.
NO synthetic fallback logic is implemented here;
fallback is handled by the main orchestration logic.
"""

import os
import logging
from typing import Optional, Dict, Any

import pandas as pd

from utils.exceptions import DataLoadError
from utils.logger import get_logger, log_data_load_start, log_data_load_success, log_data_load_error
from utils.config import get_config

# Configure logger
logger = get_logger(__name__)

# Verified real data sources
# Since no specific public dataset matches the exact longitudinal psychometric 
# requirements (engagement + Rosenberg Self-Esteem + comment sentiment + timestamps)
# in a single downloadable file, we attempt to load from a hypothetical verified
# source if provided via config, or raise a clear DataLoadError.
# In a real production scenario, this would connect to a specific repository
# (e.g., ICPSR, OSF, or a specific API).

REAL_DATA_SOURCE_URL = os.getenv(
    "SOCIAL_VALIDATION_DATA_URL",
    None  # Default to None to force explicit configuration or failure
)

# Alternative: Attempt to load from a known HuggingFace dataset if available
# For this specific research topic, no single public dataset exists that perfectly matches
# the schema. We implement the loader to attempt a fetch from a configured URL.
# If no URL is configured, it raises DataLoadError immediately.

def load_real_data(config: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Attempt to load real dataset from a configured source.
    
    Args:
        config: Optional configuration dictionary. If not provided, uses get_config().
    
    Returns:
        pd.DataFrame: The loaded dataset.
    
    Raises:
        DataLoadError: If the real dataset cannot be fetched or loaded.
        ValueError: If no data source is configured.
    """
    log_data_load_start(logger)
    
    cfg = config or get_config()
    source_url = cfg.get("data", {}).get("real_source_url", REAL_DATA_SOURCE_URL)
    
    if not source_url:
        error_msg = "DataLoadError: No real data source URL configured. " \
                    "Set SOCIAL_VALIDATION_DATA_URL or 'data.real_source_url' in config."
        logger.error(error_msg)
        log_data_load_error(logger, error_msg)
        raise DataLoadError(error_msg)
    
    try:
        logger.info(f"Attempting to fetch real data from: {source_url}")
        
        # Attempt to load based on file extension or heuristic
        if source_url.endswith(".csv"):
            # Try direct load (if local) or fetch via requests if remote
            if source_url.startswith(("http://", "https://")):
                import requests
                response = requests.get(source_url, timeout=30)
                response.raise_for_status()
                # Read from text buffer
                import io
                df = pd.read_csv(io.StringIO(response.text))
            else:
                df = pd.read_csv(source_url)
        
        elif source_url.endswith(".parquet"):
            if source_url.startswith(("http://", "https://")):
                import requests
                response = requests.get(source_url, timeout=30)
                response.raise_for_status()
                import io
                df = pd.read_parquet(io.BytesIO(response.content))
            else:
                df = pd.read_parquet(source_url)
        
        elif source_url.endswith(".json"):
            if source_url.startswith(("http://", "https://")):
                import requests
                response = requests.get(source_url, timeout=30)
                response.raise_for_status()
                df = pd.read_json(io.StringIO(response.text))
            else:
                df = pd.read_json(source_url)
        
        else:
            # Fallback: try pandas read_csv for unknown extensions or generic URLs
            if source_url.startswith(("http://", "https://")):
                import requests
                response = requests.get(source_url, timeout=30)
                response.raise_for_status()
                import io
                df = pd.read_csv(io.StringIO(response.text))
            else:
                df = pd.read_csv(source_url)
        
        if df.empty:
            error_msg = f"DataLoadError: The dataset at {source_url} was fetched but is empty."
            logger.error(error_msg)
            log_data_load_error(logger, error_msg)
            raise DataLoadError(error_msg)
        
        logger.info(f"Successfully loaded {len(df)} rows from {source_url}")
        log_data_load_success(logger, len(df))
        return df
        
    except requests.exceptions.RequestException as e:
        error_msg = f"DataLoadError: Failed to fetch real dataset from {source_url}. Network error: {str(e)}"
        logger.error(error_msg)
        log_data_load_error(logger, error_msg)
        raise DataLoadError(error_msg) from e
    except pd.errors.EmptyDataError as e:
        error_msg = f"DataLoadError: Failed to parse data from {source_url}. File is empty or malformed."
        logger.error(error_msg)
        log_data_load_error(logger, error_msg)
        raise DataLoadError(error_msg) from e
    except Exception as e:
        error_msg = f"DataLoadError: Failed to fetch real dataset from {source_url}. {type(e).__name__}: {str(e)}"
        logger.error(error_msg)
        log_data_load_error(logger, error_msg)
        raise DataLoadError(error_msg) from e


def main():
    """
    Main entry point for testing the loader standalone.
    """
    logger.info("Running loader.py main entry point.")
    try:
        df = load_real_data()
        logger.info(f"Data loaded successfully. Shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        return df
    except DataLoadError as e:
        logger.error(f"Failed to load data: {e}")
        # Re-raise so the orchestration layer can catch it
        raise


if __name__ == "__main__":
    main()