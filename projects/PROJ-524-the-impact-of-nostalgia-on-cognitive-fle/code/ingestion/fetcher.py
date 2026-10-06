import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd

from utils import log_info, log_warning, log_error

logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Exception raised when data fetching fails."""
    pass

class DataGapError(Exception):
    """Exception raised when a required data gap is detected."""
    pass

class RealDataFetchFailed(Exception):
    """Exception raised when real data fetch fails and simulation is required."""
    pass

def fetch_from_openml(dataset_id: int) -> pd.DataFrame:
    """
    Fetches data from OpenML.
    
    Args:
        dataset_id: The OpenML dataset ID.
    
    Returns:
        DataFrame with the fetched data.
    
    Raises:
        DataFetchError: If the fetch fails.
    """
    try:
        import openml
        dataset = openml.datasets.get_dataset(dataset_id)
        df, _, _, _ = dataset.get_data()
        log_info(f"Successfully fetched dataset {dataset_id} from OpenML.")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch from OpenML: {e}")
        raise DataFetchError(f"OpenML fetch failed: {e}")

def fetch_from_huggingface(path: str, config: Optional[str] = None) -> pd.DataFrame:
    """
    Fetches data from HuggingFace Datasets.
    
    Args:
        path: The dataset path.
        config: The dataset configuration name.
    
    Returns:
        DataFrame with the fetched data.
    
    Raises:
        DataFetchError: If the fetch fails.
    """
    try:
        from datasets import load_dataset
        ds = load_dataset(path, config if config else None, split="train")
        df = ds.to_pandas()
        log_info(f"Successfully fetched dataset {path} from HuggingFace.")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch from HuggingFace: {e}")
        raise DataFetchError(f"HuggingFace fetch failed: {e}")

def fetch_from_url(url: str) -> pd.DataFrame:
    """
    Fetches data from a URL (CSV).
    
    Args:
        url: The URL to the CSV file.
    
    Returns:
        DataFrame with the fetched data.
    
    Raises:
        DataFetchError: If the fetch fails.
    """
    try:
        df = pd.read_csv(url)
        log_info(f"Successfully fetched data from {url}.")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch from URL: {e}")
        raise DataFetchError(f"URL fetch failed: {e}")

def fetch_metadata_from_source(source: str) -> Dict[str, Any]:
    """
    Fetches metadata from a source.
    
    Args:
        source: The source identifier.
    
    Returns:
        Dictionary with metadata.
    """
    return {"source": source, "fetched_at": pd.Timestamp.now().isoformat()}

def load_local_file(filepath: str) -> pd.DataFrame:
    """
    Loads data from a local file.
    
    Args:
        filepath: Path to the file.
    
    Returns:
        DataFrame with the loaded data.
    """
    df = pd.read_csv(filepath)
    log_info(f"Successfully loaded local file {filepath}.")
    return df

def fetch_data() -> Tuple[Optional[pd.DataFrame], str, bool]:
    """
    Attempts to fetch real data from the canonical source.
    
    Tries OpenML, then HuggingFace, then URL.
    If all fail, raises RealDataFetchFailed.
    
    Returns:
        Tuple of (DataFrame, source_name, simulation_mode).
    
    Raises:
        RealDataFetchFailed: If real data cannot be fetched.
    """
    # Check for verified source override
    verified_path = Path("data/verified_source.json")
    if verified_path.exists():
        with open(verified_path, 'r') as f:
            verified = json.load(f)
        source_type = verified.get("type")
        source_id = verified.get("id")
        log_info(f"Using verified source: {source_type} - {source_id}")
        
        if source_type == "openml":
            try:
                df = fetch_from_openml(int(source_id))
                return df, source_id, False
            except DataFetchError:
                log_warning("Verified source fetch failed.")
        
        elif source_type == "huggingface":
            try:
                df = fetch_from_huggingface(source_id, verified.get("config"))
                return df, source_id, False
            except DataFetchError:
                log_warning("Verified source fetch failed.")
        
        elif source_type == "url":
            try:
                df = fetch_from_url(source_id)
                return df, source_id, False
            except DataFetchError:
                log_warning("Verified source fetch failed.")

    # Try canonical sources defined in plan.md
    # 1. OpenML WCST dataset (example ID)
    try:
        df = fetch_from_openml(12345) # Placeholder ID, will fail if not real
        return df, "openml_12345", False
    except DataFetchError:
        log_info("OpenML fetch failed.")
    
    # 2. HuggingFace dataset
    try:
        df = fetch_from_huggingface("some_real_wcst_dataset", "default")
        return df, "huggingface_some_real_wcst_dataset", False
    except DataFetchError:
        log_info("HuggingFace fetch failed.")
    
    # 3. Direct URL
    try:
        df = fetch_from_url("https://example.com/wcst_data.csv")
        return df, "url_example", False
    except DataFetchError:
        log_info("URL fetch failed.")
    
    # All real sources failed
    log_error("All real data sources failed to fetch.")
    raise RealDataFetchFailed("Could not fetch real data from any canonical source.")

def save_metadata(metadata: Dict[str, Any], filepath: str) -> None:
    """
    Saves metadata to a JSON file.
    
    Args:
        metadata: Metadata dictionary.
        filepath: Path to save the file.
    """
    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2)
    log_info(f"Metadata saved to {filepath}")

def save_exclusion_log(exclusion_counts: Dict[str, int], filepath: str) -> None:
    """
    Saves exclusion log to a JSON file.
    
    Args:
        exclusion_counts: Dictionary of exclusion counts.
        filepath: Path to save the file.
    """
    with open(filepath, 'w') as f:
        json.dump(exclusion_counts, f, indent=2)
    log_info(f"Exclusion log saved to {filepath}")
