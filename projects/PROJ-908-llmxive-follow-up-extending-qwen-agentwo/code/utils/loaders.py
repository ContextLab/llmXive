"""
Data Loaders for llmXive Pipeline.

This module provides strict real-data fetching utilities.
- No synthetic fallbacks are allowed.
- If a real source is unavailable, the function must raise an exception.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

def load_cot_traces(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Loads Chain-of-Thought traces from a JSON file.
    
    Args:
        file_path: Path to the JSON file (e.g., 'data/raw/cot_traces.json').
        
    Returns:
        List of trace dictionaries.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CoT traces file not found: {path}. "
                                "Ensure T020 has run to generate this file.")
    
    logger.info(f"Loading CoT traces from {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of traces in {path}, got {type(data)}")
    
    return data

def load_oracle_source_code(file_path: Union[str, Path]) -> str:
    """
    Loads the source code text for the Oracle parser/simulator.
    
    Args:
        file_path: Path to the source file.
        
    Returns:
        String content of the source file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def load_dataset_from_url(url: str, cache_dir: Optional[str] = None) -> Any:
    """
    Loads a dataset from a URL using the `datasets` library or standard requests.
    
    This function strictly fails if the download fails. No synthetic data is generated.
    
    Args:
        url: URL to the dataset (e.g., Hugging Face dataset URL or direct file link).
        cache_dir: Optional directory to cache the dataset.
        
    Returns:
        The loaded dataset object or raw data.
        
    Raises:
        Exception: If the download or loading fails.
    """
    try:
        from datasets import load_dataset
        logger.info(f"Attempting to load dataset from {url}...")
        # If it's a HF dataset path
        if url.startswith("http"):
            # Try to load as a generic dataset if it's a HF repo
            # This is a simplified wrapper; specific logic depends on the dataset format
            ds = load_dataset(url, cache_dir=cache_dir)
        else:
            # Assume it's a HF dataset ID
            ds = load_dataset(url, cache_dir=cache_dir)
        
        logger.info("Dataset loaded successfully.")
        return ds
    except ImportError:
        logger.error("The 'datasets' library is required. Install with: pip install datasets")
        raise
    except Exception as e:
        logger.error(f"Failed to load dataset from {url}: {e}")
        # Fail loudly as per constraints
        raise RuntimeError(f"Real data source {url} is unavailable. Cannot proceed without real data.") from e
