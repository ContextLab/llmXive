import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd
from datasets import load_dataset

logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Raised when a data fetch operation fails."""
    pass

class DataGapError(Exception):
    """Raised when a required data segment is missing."""
    pass

class RealDataFetchFailed(Exception):
    """Raised specifically when real data fetch fails and no fallback is allowed."""
    pass

def fetch_from_openml(dataset_id: int) -> pd.DataFrame:
    """
    Fetch data from OpenML by ID.
    
    Args:
        dataset_id: The OpenML dataset ID.
        
    Returns:
        A pandas DataFrame containing the dataset.
        
    Raises:
        DataFetchError: If the fetch fails.
    """
    try:
        # OpenML integration via datasets library or direct API
        # Using HuggingFace datasets for OpenML compatibility where possible
        # or direct fetch if specific OpenML package is preferred.
        # For this implementation, we attempt to load via datasets if available 
        # or raise if not found to ensure explicit failure.
        logger.info(f"Attempting to fetch OpenML dataset ID: {dataset_id}")
        
        # Note: Direct OpenML fetch via `openml` package is standard, 
        # but `datasets` is the primary dependency listed. 
        # We will use `openml` if available, otherwise fallback to a generic URL fetch strategy
        # if the dataset is hosted elsewhere, or raise an explicit error if no source is found.
        
        # Since the dependency list includes 'datasets' but not explicitly 'openml',
        # and OpenML datasets are often mirrored or accessible via specific IDs in HF,
        # we will attempt a generic fetch mechanism or raise if the specific ID isn't
        # mapped to a known HF path.
        
        # However, to strictly follow "Real data only" and "Fail loudly":
        # We will attempt to fetch from a known real source if the ID is standard.
        # If not, we raise.
        
        # Attempting to use the `openml` library if installed, else raising
        # to force the user to install it or provide a verified source.
        try:
            import openml
            dataset = openml.datasets.get_dataset(dataset_id)
            X, y, categorical, target = dataset.get_data(dataset_format="dataframe", target=target)
            return X
        except ImportError:
            logger.warning("OpenML library not installed. Attempting alternative fetch.")
            # Fallback to a generic URL fetch if we have a mapping, else fail
            raise DataFetchError(f"OpenML library required for ID {dataset_id} but not installed.")
            
    except Exception as e:
        logger.error(f"Failed to fetch data from OpenML ID {dataset_id}: {e}")
        raise DataFetchError(f"Failed to fetch data from OpenML ID {dataset_id}: {e}")

def fetch_from_huggingface(path: str, split: str = "train") -> pd.DataFrame:
    """
    Fetch data from HuggingFace Datasets.
    
    Args:
        path: The dataset path (e.g., 'username/dataset_name').
        split: The dataset split to load.
        
    Returns:
        A pandas DataFrame.
        
    Raises:
        DataFetchError: If the fetch fails.
    """
    try:
        logger.info(f"Attempting to fetch HuggingFace dataset: {path}, split: {split}")
        dataset = load_dataset(path, split=split)
        return dataset.to_pandas()
    except Exception as e:
        logger.error(f"Failed to fetch data from HuggingFace {path}: {e}")
        raise DataFetchError(f"Failed to fetch data from HuggingFace {path}: {e}")

def fetch_from_url(url: str) -> pd.DataFrame:
    """
    Fetch data from a direct CSV/JSON URL.
    
    Args:
        url: The URL to the data file.
        
    Returns:
        A pandas DataFrame.
        
    Raises:
        DataFetchError: If the fetch fails.
    """
    try:
        logger.info(f"Attempting to fetch data from URL: {url}")
        if url.endswith('.csv'):
            df = pd.read_csv(url)
        elif url.endswith('.json'):
            df = pd.read_json(url)
        else:
            raise DataFetchError(f"Unsupported file format for URL: {url}")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch data from URL {url}: {e}")
        raise DataFetchError(f"Failed to fetch data from URL {url}: {e}")

def fetch_metadata_from_source(source_type: str, source_id: str) -> Dict[str, Any]:
    """
    Fetch metadata associated with a data source.
    
    Args:
        source_type: Type of source ('openml', 'huggingface', 'url').
        source_id: The ID or path of the source.
        
    Returns:
        A dictionary containing metadata.
    """
    # Placeholder for metadata fetching logic
    return {
        "source_type": source_type,
        "source_id": source_id,
        "fetched_at": pd.Timestamp.now().isoformat()
    }

def load_local_file(path: str) -> pd.DataFrame:
    """
    Load a local file (CSV/JSON).
    
    Args:
        path: Path to the local file.
        
    Returns:
        A pandas DataFrame.
        
    Raises:
        DataFetchError: If the file cannot be loaded.
    """
    try:
        logger.info(f"Loading local file: {path}")
        if path.endswith('.csv'):
            return pd.read_csv(path)
        elif path.endswith('.json'):
            return pd.read_json(path)
        else:
            raise DataFetchError(f"Unsupported file format: {path}")
    except Exception as e:
        logger.error(f"Failed to load local file {path}: {e}")
        raise DataFetchError(f"Failed to load local file {path}: {e}")

def generate_synthetic_fallback(n_samples: int = 100) -> pd.DataFrame:
    """
    Generate synthetic data as a fallback.
    
    NOTE: This function is for fallback ONLY if explicitly allowed by the orchestration logic.
    T010a strictly forbids using this in `fetch_data`.
    
    Args:
        n_samples: Number of samples to generate.
        
    Returns:
        A synthetic DataFrame.
    """
    logger.warning("Generating synthetic fallback data. This should not be used in T010a.")
    import numpy as np
    data = {
        'participant_id': [f"P{i}" for i in range(n_samples)],
        'age': np.random.randint(65, 85, n_samples),
        'stimulus_type': np.random.choice(['nostalgia', 'control'], n_samples),
        'perseverative_errors': np.random.normal(10, 3, n_samples),
        'categories_completed': np.random.normal(5, 1, n_samples),
        'MMSE': np.random.normal(28, 2, n_samples)
    }
    return pd.DataFrame(data)

def fetch_data() -> Tuple[Optional[pd.DataFrame], str, bool]:
    """
    Attempt to fetch real data from a canonical source.
    
    Logic:
    1. Check for a "VERIFIED REAL DATA SOURCE" block in the environment or config.
    2. If present, use the specified source.
    3. If not, attempt to fetch from a predefined canonical source (e.g., OpenML ID 40945 - a common WCST-like dataset or similar).
    4. If fetch succeeds, save to data/raw/raw_dataset.csv and return success.
    5. If fetch fails, raise RealDataFetchFailed.
    
    Returns:
        Tuple of (DataFrame, source_string, simulation_mode_bool).
        
    Raises:
        RealDataFetchFailed: If real data cannot be fetched.
    """
    config_source = os.getenv("VERIFIED_DATA_SOURCE", None)
    
    if config_source:
        logger.info(f"Using verified data source from environment: {config_source}")
        try:
            # Parse config_source (expected format: "type:id" or "url:path")
            if config_source.startswith("openml:"):
                dataset_id = int(config_source.split(":")[1])
                df = fetch_from_openml(dataset_id)
                source = f"openml:{dataset_id}"
            elif config_source.startswith("hf:"):
                path = config_source.split("hf:")[1]
                df = fetch_from_huggingface(path)
                source = f"hf:{path}"
            elif config_source.startswith("url:"):
                url = config_source.split("url:")[1]
                df = fetch_from_url(url)
                source = f"url:{url}"
            else:
                # Try to load as local file if it looks like a path
                if os.path.exists(config_source):
                    df = load_local_file(config_source)
                    source = f"local:{config_source}"
                else:
                    raise DataFetchError(f"Unknown source format: {config_source}")
            
            if df is not None and not df.empty:
                # Save raw dataset immediately
                raw_path = Path("data/raw/raw_dataset.csv")
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(raw_path, index=False)
                logger.info(f"Raw dataset saved to {raw_path}")
                return df, source, False
            else:
                raise DataFetchError("Fetched data is empty.")
                
        except Exception as e:
            logger.error(f"Failed to fetch from verified source {config_source}: {e}")
            raise RealDataFetchFailed(f"Failed to fetch from verified source: {e}")
    
    # Canonical fallback attempt if no verified source is set
    # Attempting to fetch a real WCST dataset. 
    # OpenML ID 40945 is a common dataset for cognitive tasks, or we can try a specific HuggingFace dataset.
    # If these fail, we MUST raise RealDataFetchFailed.
    
    canonical_sources = [
        ("openml", 40945), # Example ID, may need adjustment based on actual availability
        ("hf", "mlfoundations/wcst_data"), # Hypothetical path
    ]
    
    for source_type, source_id in canonical_sources:
        try:
            if source_type == "openml":
                df = fetch_from_openml(source_id)
                source = f"openml:{source_id}"
            elif source_type == "hf":
                df = fetch_from_huggingface(source_id)
                source = f"hf:{source_id}"
            
            if df is not None and not df.empty:
                raw_path = Path("data/raw/raw_dataset.csv")
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(raw_path, index=False)
                logger.info(f"Raw dataset saved to {raw_path}")
                return df, source, False
        except Exception as e:
            logger.warning(f"Source {source_type}:{source_id} failed: {e}")
            continue
    
    # If all attempts fail
    error_msg = "Failed to fetch real data from any canonical source. RealDataFetchFailed raised."
    logger.error(error_msg)
    raise RealDataFetchFailed(error_msg)

def save_metadata(metadata: Dict[str, Any], path: str) -> None:
    """Save metadata to a JSON file."""
    with open(path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved to {path}")

def save_exclusion_log(exclusion_counts: Dict[str, Any], path: str) -> None:
    """Save exclusion log to a JSON file."""
    with open(path, 'w') as f:
        json.dump(exclusion_counts, f, indent=2)
    logger.info(f"Exclusion log saved to {path}")
