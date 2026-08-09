"""
Data Fetching Module for Nostalgia-Cognitive Flexibility Study.

This module handles all external data retrieval operations, separating
fetching logic from schema validation to improve modularity.

Includes:
- OpenML dataset search and retrieval
- HuggingFace dataset search and retrieval
- Direct URL fetching
- Metadata extraction

All fetchers raise DataFetchError on failure and do NOT fallback to synthetic data.
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import pandas as pd

# Import shared exceptions and config
try:
    from config import get_config, get_env_bool, get_data_source_url
    from utils import setup_logging, log_info, log_warning, log_error, compute_sha256
except ImportError:
    # Fallback for direct module execution during testing
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import get_config, get_env_bool, get_data_source_url
    from utils import setup_logging, log_info, log_warning, log_error, compute_sha256

# Define custom exceptions locally if not imported from a shared module
# (Assuming they are defined in ingestion.py or utils, but re-defining here for clarity in the split module)
class DataFetchError(Exception):
    """Raised when data fetching fails from all sources."""
    pass

class DataGapError(Exception):
    """Raised when no valid real dataset is found and simulation is not explicitly allowed."""
    pass

# Setup logging
logger = logging.getLogger(__name__)

def _search_openml_datasets(keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Dynamically search OpenML for datasets containing specific keywords.
    
    Args:
        keywords: List of keywords to search for (e.g., "WCST", "cognitive", "aging")
        
    Returns:
        List of matching dataset metadata dictionaries.
    """
    try:
        import openml
        log_info(logger, f"Searching OpenML for keywords: {keywords}")
        
        # OpenML search API
        # We search for datasets with the keywords in the description or name
        # Note: OpenML search is case-insensitive by default
        all_matches = []
        
        for keyword in keywords:
            try:
                datasets = openml.datasets.list_datasets(search=keyword, output_format="dataframe")
                if datasets is not None and not datasets.empty:
                    # Convert to list of dicts for easier processing
                    for _, row in datasets.iterrows():
                        match = {
                            "dataset_id": row.get("did"),
                            "name": row.get("name"),
                            "description": row.get("description"),
                            "source": "openml",
                            "keyword_match": keyword
                        }
                        # Avoid duplicates based on dataset_id
                        if not any(m["dataset_id"] == match["dataset_id"] for m in all_matches):
                            all_matches.append(match)
                            log_info(logger, f"Found OpenML dataset: {match['name']} (ID: {match['dataset_id']})")
            except Exception as e:
                log_warning(logger, f"Error searching OpenML for keyword '{keyword}': {e}")
                continue
        
        return all_matches
    except ImportError:
        raise DataFetchError("OpenML library not installed. Install with 'pip install openml'")
    except Exception as e:
        log_error(logger, f"Failed to search OpenML: {e}")
        raise DataFetchError(f"OpenML search failed: {e}")

def _search_huggingface_datasets(keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Dynamically search HuggingFace Datasets for matching datasets.
    
    Args:
        keywords: List of keywords to search for.
        
    Returns:
        List of matching dataset metadata dictionaries.
    """
    try:
        from datasets import list_datasets
        log_info(logger, f"Searching HuggingFace for keywords: {keywords}")
        
        all_matches = []
        # HuggingFace list_datasets doesn't take search keywords directly in the same way
        # We list available datasets and filter by description/name if possible
        # Note: list_datasets() without args returns all datasets, which is huge.
        # We will try to filter by searching the 'tags' or 'description' if the API supports it.
        # The `datasets` library's `list_datasets` doesn't have a direct search param like OpenML.
        # We will fetch a subset or rely on the user to specify a specific dataset ID if search fails.
        # However, for this task, we attempt to use the `search` parameter if available in newer versions
        # or fallback to a manual check if we had a specific list.
        
        # Since `list_datasets` doesn't support search, we will try to fetch a specific dataset if
        # the user has provided a hint, or we search for a known pattern if possible.
        # For this implementation, we assume we might need to check specific known datasets
        # or the user provides a specific ID. But the task asks for dynamic search.
        # Let's try to use the `search` argument if the underlying API supports it (it might in newer versions).
        # If not, we log a warning that we cannot search dynamically and require a specific ID.
        
        # Attempting to use search if available (checking via getattr or try/except)
        try:
            # Try to search - this might not work for all HF datasets but worth a try
            # Note: As of current HF versions, list_datasets doesn't support 'search'.
            # We will simulate a search by checking a small sample or raising a specific error
            # if dynamic search isn't supported, forcing the user to specify.
            # However, to satisfy the "dynamic search" requirement, we will try to fetch
            # datasets with specific tags or names if we can construct a query.
            # Since we can't easily search all HF, we will log that we are looking for specific IDs
            # or rely on the fact that the user might have configured a specific dataset.
            
            # Fallback strategy: We will try to fetch a known dataset ID if keywords match known patterns
            # or raise DataGapError if no match.
            # But the task says "Dynamically search". Let's try to use `datasets`'s `search` if it exists.
            # It doesn't. So we will raise a specific error indicating we need a specific ID.
            # OR, we can try to use the `huggingface_hub` library to search.
            
            from huggingface_hub import HfApi
            api = HfApi()
            # Search for datasets
            for keyword in keywords:
                try:
                    # Search for datasets with the keyword
                    results = api.list_datasets(search=keyword, limit=10)
                    for ds in results:
                        match = {
                            "dataset_id": ds.id,
                            "name": ds.id,
                            "description": ds.description,
                            "source": "huggingface",
                            "keyword_match": keyword
                        }
                        if not any(m["dataset_id"] == match["dataset_id"] for m in all_matches):
                            all_matches.append(match)
                            log_info(logger, f"Found HuggingFace dataset: {match['name']}")
                except Exception as e:
                    log_warning(logger, f"Error searching HuggingFace for '{keyword}': {e}")
                    continue
        except ImportError:
            log_warning(logger, "huggingface_hub not installed. Skipping HuggingFace search.")
        
        return all_matches
    except Exception as e:
        log_error(logger, f"Failed to search HuggingFace: {e}")
        raise DataFetchError(f"HuggingFace search failed: {e}")

def fetch_from_openml(dataset_id: int) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Fetch a dataset from OpenML by ID.
    
    Args:
        dataset_id: The OpenML dataset ID.
        
    Returns:
        Tuple of (DataFrame, metadata_dict)
        
    Raises:
        DataFetchError: If the dataset cannot be fetched.
    """
    try:
        import openml
        log_info(logger, f"Fetching OpenML dataset ID: {dataset_id}")
        
        dataset = openml.datasets.get_dataset(dataset_id)
        X, y, categorical_indicator, attribute_names = dataset.get_data(
            dataset_format="dataframe", target=dataset.default_target_attribute
        )
        
        # Construct metadata
        metadata = {
            "source": "openml",
            "dataset_id": dataset_id,
            "name": dataset.name,
            "description": dataset.description,
            "citation": dataset.citation,
            "features": list(X.columns) if X is not None else []
        }
        
        log_info(logger, f"Successfully fetched OpenML dataset: {dataset.name}")
        return X, metadata
    except ImportError:
        raise DataFetchError("OpenML library not installed.")
    except Exception as e:
        log_error(logger, f"Failed to fetch OpenML dataset {dataset_id}: {e}")
        raise DataFetchError(f"OpenML fetch failed: {e}")

def fetch_from_huggingface(dataset_id: str, split: str = "train") -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Fetch a dataset from HuggingFace by ID.
    
    Args:
        dataset_id: The HuggingFace dataset ID (e.g., "username/dataset_name").
        split: The split to load (default "train").
        
    Returns:
        Tuple of (DataFrame, metadata_dict)
        
    Raises:
        DataFetchError: If the dataset cannot be fetched.
    """
    try:
        from datasets import load_dataset
        log_info(logger, f"Fetching HuggingFace dataset: {dataset_id}")
        
        # Load dataset
        ds = load_dataset(dataset_id, split=split)
        df = ds.to_pandas()
        
        metadata = {
            "source": "huggingface",
            "dataset_id": dataset_id,
            "split": split,
            "num_rows": len(df),
            "features": list(df.columns),
            "citation": ds.info.citation if hasattr(ds, 'info') else None
        }
        
        log_info(logger, f"Successfully fetched HuggingFace dataset: {dataset_id}")
        return df, metadata
    except ImportError:
        raise DataFetchError("datasets library not installed.")
    except Exception as e:
        log_error(logger, f"Failed to fetch HuggingFace dataset {dataset_id}: {e}")
        raise DataFetchError(f"HuggingFace fetch failed: {e}")

def fetch_from_url(url: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Fetch a dataset from a direct URL (CSV, JSON, etc.).
    
    Args:
        url: The URL to the data file.
        
    Returns:
        Tuple of (DataFrame, metadata_dict)
        
    Raises:
        DataFetchError: If the file cannot be fetched or parsed.
    """
    import requests
    try:
        log_info(logger, f"Fetching dataset from URL: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Try to detect format and parse
        if url.endswith('.csv'):
            df = pd.read_csv(pd.io.common.BytesIO(response.content))
        elif url.endswith('.json'):
            df = pd.read_json(pd.io.common.BytesIO(response.content))
        else:
            # Try CSV first
            try:
                df = pd.read_csv(pd.io.common.BytesIO(response.content))
            except:
                raise ValueError("Unsupported file format. Only CSV/JSON supported.")
        
        metadata = {
            "source": "url",
            "url": url,
            "num_rows": len(df),
            "features": list(df.columns)
        }
        
        log_info(logger, f"Successfully fetched dataset from URL")
        return df, metadata
    except ImportError:
        raise DataFetchError("requests library not installed.")
    except Exception as e:
        log_error(logger, f"Failed to fetch dataset from URL {url}: {e}")
        raise DataFetchError(f"URL fetch failed: {e}")

def fetch_metadata_from_source(source_type: str, source_id: str) -> Dict[str, Any]:
    """
    Fetch metadata for a dataset from its source.
    
    Args:
        source_type: One of 'openml', 'huggingface', 'url'.
        source_id: The ID or URL of the dataset.
        
    Returns:
        Metadata dictionary.
        
    Raises:
        DataFetchError: If metadata cannot be fetched.
    """
    try:
        if source_type == 'openml':
            # OpenML metadata is fetched with the data, but we can fetch just metadata if needed
            import openml
            dataset = openml.datasets.get_dataset(int(source_id))
            return {
                "source": "openml",
                "dataset_id": int(source_id),
                "name": dataset.name,
                "description": dataset.description,
                "citation": dataset.citation,
                "features": [] # Features are fetched with data
            }
        elif source_type == 'huggingface':
            from datasets import load_dataset
            ds = load_dataset(source_id, split="train", streaming=True)
            # Get info
            info = ds.info
            return {
                "source": "huggingface",
                "dataset_id": source_id,
                "citation": info.citation,
                "description": info.description,
                "features": []
            }
        elif source_type == 'url':
            # For URL, metadata is usually not separate
            return {
                "source": "url",
                "url": source_id
            }
        else:
            raise ValueError(f"Unknown source type: {source_type}")
    except Exception as e:
        log_error(logger, f"Failed to fetch metadata from {source_type}: {e}")
        raise DataFetchError(f"Metadata fetch failed: {e}")

def load_local_file(file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load a dataset from a local file.
    
    Args:
        file_path: Path to the local file.
        
    Returns:
        Tuple of (DataFrame, metadata_dict)
        
    Raises:
        DataFetchError: If the file cannot be loaded.
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Local file not found: {file_path}")
        
        log_info(logger, f"Loading local file: {file_path}")
        
        if path.suffix == '.csv':
            df = pd.read_csv(path)
        elif path.suffix == '.json':
            df = pd.read_json(path)
        else:
            df = pd.read_csv(path) # Default to CSV
        
        metadata = {
            "source": "local",
            "file_path": str(path),
            "num_rows": len(df),
            "features": list(df.columns)
        }
        
        log_info(logger, f"Successfully loaded local file")
        return df, metadata
    except Exception as e:
        log_error(logger, f"Failed to load local file {file_path}: {e}")
        raise DataFetchError(f"Local file load failed: {e}")

def fetch_data(keywords: List[str] = None, dataset_id: int = None, url: str = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main entry point for fetching data.
    
    Strategy:
    1. If dataset_id is provided, fetch directly from OpenML.
    2. If url is provided, fetch from URL.
    3. If keywords are provided, search OpenML and HuggingFace.
    4. If no match found, raise DataGapError.
    
    Args:
        keywords: List of keywords to search (e.g., ["WCST", "aging"]).
        dataset_id: Specific OpenML dataset ID.
        url: Specific URL to fetch.
        
    Returns:
        Tuple of (DataFrame, metadata_dict)
        
    Raises:
        DataFetchError: If fetching fails.
        DataGapError: If no real dataset is found.
    """
    config = get_config()
    sim_mode = get_env_bool("SIMULATION_MODE", False)
    
    if dataset_id is not None:
        log_info(logger, f"Fetching specific OpenML dataset ID: {dataset_id}")
        return fetch_from_openml(dataset_id)
    
    if url is not None:
        log_info(logger, f"Fetching specific URL: {url}")
        return fetch_from_url(url)
    
    if keywords is None:
        keywords = ["WCST", "cognitive", "aging", "executive function"]
    
    log_info(logger, f"Searching for datasets with keywords: {keywords}")
    
    # 1. Search OpenML
    openml_matches = _search_openml_datasets(keywords)
    if openml_matches:
        # Try to fetch the first match
        match = openml_matches[0]
        log_info(logger, f"Attempting to fetch OpenML dataset: {match['name']}")
        try:
            df, meta = fetch_from_openml(match['dataset_id'])
            meta.update(match) # Add search match info
            return df, meta
        except DataFetchError as e:
            log_warning(logger, f"Failed to fetch top OpenML match: {e}")
            # Try next? For now, just fail if top one fails to keep it simple
            # Or try all matches? Let's try all matches
            for m in openml_matches[1:]:
                try:
                    df, meta = fetch_from_openml(m['dataset_id'])
                    meta.update(m)
                    return df, meta
                except:
                    continue
    
    # 2. Search HuggingFace
    hf_matches = _search_huggingface_datasets(keywords)
    if hf_matches:
        match = hf_matches[0]
        log_info(logger, f"Attempting to fetch HuggingFace dataset: {match['name']}")
        try:
            df, meta = fetch_from_huggingface(match['dataset_id'])
            meta.update(match)
            return df, meta
        except DataFetchError as e:
            log_warning(logger, f"Failed to fetch top HuggingFace match: {e}")
            for m in hf_matches[1:]:
                try:
                    df, meta = fetch_from_huggingface(m['dataset_id'])
                    meta.update(m)
                    return df, meta
                except:
                    continue
    
    # No data found
    log_error(logger, "No valid real dataset found after searching OpenML and HuggingFace.")
    if sim_mode:
        log_warning(logger, "SIMULATION_MODE is True. Proceeding to simulation mode (if allowed by caller).")
        raise DataGapError("No real data found. SIMULATION_MODE enabled.")
    else:
        raise DataGapError("No real data found and SIMULATION_MODE is False. Halting.")

def fetch_metadata_from_url(url: str) -> Dict[str, Any]:
    """
    Fetch metadata from a URL (if available) or return basic info.
    
    Args:
        url: The URL.
        
    Returns:
        Metadata dictionary.
    """
    try:
        import requests
        # Try to get headers or a specific metadata endpoint if known
        # For generic URLs, we just return the URL as source
        return {
            "source": "url",
            "url": url,
            "fetched_at": os.popen("date -u +%Y-%m-%dT%H:%M:%SZ").read().strip()
        }
    except Exception as e:
        log_warning(logger, f"Could not fetch metadata from URL: {e}")
        return {
            "source": "url",
            "url": url
        }
