"""
Data ingestion module for fetching and validating datasets.
Implements dynamic search for WCST/Executive Function datasets on OpenML and HuggingFace.
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd
import openml
from datasets import list_datasets as hf_list_datasets, load_dataset

from config import get_config, get_env_bool, get_mmse_threshold, ensure_dirs, log_info, log_warning
from utils import setup_logging, log_error, log_critical, compute_sha256

# Setup logging
_logger = setup_logging("ingestion")


class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass


class DataGapError(Exception):
    """Custom exception when no valid real dataset is found."""
    pass


def fetch_metadata_from_source(source_type: str, dataset_id: int) -> Dict[str, Any]:
    """
    Fetches metadata for a dataset from OpenML.
    """
    try:
        if source_type == "openml":
          dataset = openml.datasets.get_dataset(dataset_id)
          return {
              "source": "openml",
              "id": dataset_id,
              "name": dataset.name,
              "description": dataset.description,
              "features": dataset.features,
              "data_url": dataset.url
          }
        else:
          _logger.error(f"Unsupported source type: {source_type}")
          return {}
    except Exception as e:
        _logger.error(f"Failed to fetch metadata from {source_type} ID {dataset_id}: {e}")
        return {}


def load_local_file(path: str) -> Optional[pd.DataFrame]:
    """
    Loads a dataset from a local CSV file.
    """
    try:
        df = pd.read_csv(path)
        _logger.info(f"Loaded local dataset from {path} with {len(df)} rows.")
        return df
    except Exception as e:
        _logger.error(f"Failed to load local file {path}: {e}")
        return None


def _check_schema_compatibility(df: pd.DataFrame, required_cols: List[str]) -> bool:
    """
    Checks if the dataframe contains all required columns.
    """
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        _logger.warning(f"Dataset missing required columns: {missing}")
        return False
    return True


def fetch_from_openml(keywords: List[str]) -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Any]]]:
    """
    Dynamically searches OpenML for datasets containing keywords and fetches the first valid match.
    Returns (DataFrame, Metadata) or (None, None) if no match found.
    """
    required_cols = ["age", "stimulus_type", "perseverative_errors", "categories_completed"]
    
    # OpenML list_datasets doesn't support keyword filtering directly in the API in a simple way
    # We will search by name/description if possible, but usually we fetch by ID.
    # Strategy: Try to find a known WCST dataset ID or search broadly if we had a search API.
    # Since OpenML search is limited in the Python wrapper without a search server, 
    # we will attempt to fetch specific known IDs related to cognitive tasks if available,
    # or iterate a small set of potential IDs if the user hasn't provided a search term.
    # However, the task asks to "Dynamically search". OpenML's search endpoint is not fully exposed 
    # in the standard `openml.datasets.list_datasets()` without filters.
    # We will try to list datasets and filter by name if we can, but this is slow.
    # Alternative: Use the openml search API directly via requests if list_datasets is too slow.
    
    # Let's try a heuristic: search for datasets with "WCST" or "Cognitive" in the name.
    # We'll use the openml search endpoint if available, otherwise we rely on the user
    # to have set a specific ID or we fail loudly as per T010a requirements if no real data.
    
    # Since `openml.datasets.list_datasets()` returns an iterator of IDs, we can't filter by text easily.
    # We will attempt to fetch a few known IDs that might match or fail.
    # But strictly following "Dynamically search": we must find a dataset matching keywords.
    # OpenML Search API (https://api.openml.org/v1/data/list/json) supports 'data_name' or 'tag'.
    
    import requests
    
    search_terms = keywords
    found_dataset = None
    
    for term in search_terms:
        try:
            # Search OpenML for datasets with the term in the name
            url = f"https://api.openml.org/v1/data/list/json"
            params = {"data_name": term, "limit": 5}
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data and len(data["data"]) > 0:
                    # Found a match
                    dataset_info = data["data"][0]
                    dataset_id = int(dataset_info["did"])
                    _logger.info(f"Found OpenML dataset '{dataset_info['name']}' (ID: {dataset_id}) matching '{term}'")
                    
                    # Fetch the dataset
                    try:
                        dataset = openml.datasets.get_dataset(dataset_id)
                        df, _ = dataset.get_data()
                        
                        if _check_schema_compatibility(df, required_cols):
                            _logger.info(f"Dataset '{dataset_info['name']}' matches schema.")
                            metadata = {
                                "source": "openml",
                                "id": dataset_id,
                                "name": dataset_info["name"],
                                "description": dataset_info.get("description", ""),
                                "url": dataset.url
                            }
                            return df, metadata
                        else:
                            _logger.warning(f"Dataset '{dataset_info['name']}' found but schema mismatch.")
                    except Exception as e:
                        _logger.warning(f"Failed to fetch OpenML dataset ID {dataset_id}: {e}")
            else:
                _logger.warning(f"OpenML search for '{term}' returned status {resp.status_code}")
        except Exception as e:
            _logger.warning(f"Error searching OpenML for '{term}': {e}")
    
    return None, None


def fetch_from_huggingface(keywords: List[str]) -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Any]]]:
    """
    Dynamically searches HuggingFace for datasets containing keywords and fetches the first valid match.
    """
    required_cols = ["age", "stimulus_type", "perseverative_errors", "categories_completed"]
    
    # HuggingFace list_datasets returns an iterator of dataset objects (name, description, etc.)
    # We filter by keywords in name or description
    _logger.info(f"Searching HuggingFace for keywords: {keywords}")
    
    try:
        # limit to 50 to avoid timeout, search is efficient
        all_datasets = list(hf_list_datasets(limit=100))
    except Exception as e:
        _logger.error(f"Failed to list HuggingFace datasets: {e}")
        return None, None
    
    for ds_info in all_datasets:
        ds_name = ds_info.id
        ds_desc = ds_info.description or ""
        ds_tags = ds_info.tags or []
        
        # Check if any keyword is in name, description, or tags
        match = False
        for kw in keywords:
            if kw.lower() in ds_name.lower() or kw.lower() in ds_desc.lower():
                match = True
                break
            # Check tags if available
            for tag in ds_tags:
                if kw.lower() in tag.lower():
                    match = True
                    break
            if match: break
        
        if match:
            _logger.info(f"Found HuggingFace dataset: {ds_name}")
            try:
                # Load the dataset (assuming default split)
                dataset = load_dataset(ds_name, split="train")
                df = dataset.to_pandas()
                
                if _check_schema_compatibility(df, required_cols):
                    _logger.info(f"HuggingFace dataset '{ds_name}' matches schema.")
                    metadata = {
                        "source": "huggingface",
                        "id": ds_name,
                        "name": ds_name,
                        "description": ds_desc,
                        "url": f"https://huggingface.co/datasets/{ds_name}"
                    }
                    return df, metadata
                else:
                    _logger.warning(f"HuggingFace dataset '{ds_name}' schema mismatch.")
            except Exception as e:
                _logger.warning(f"Failed to load HuggingFace dataset '{ds_name}': {e}")
    
    return None, None


def fetch_from_url(url: str) -> Optional[pd.DataFrame]:
    """
    Fetches data from a direct URL.
    """
    try:
        df = pd.read_csv(url)
        _logger.info(f"Loaded dataset from URL: {url}")
        return df
    except Exception as e:
        _logger.error(f"Failed to load data from URL {url}: {e}")
        return None


def fetch_metadata_from_url(url: str) -> Dict[str, Any]:
    """
    Fetches metadata from a URL (placeholder for now).
    """
    return {"url": url, "source": "url"}


def load_dataset(keywords: List[str]) -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Any]]]:
    """
    Main entry point to load a dataset.
    Searches OpenML first, then HuggingFace.
    Raises DataGapError if no valid real dataset is found and SIMULATION_MODE is not set.
    """
    _logger.info("Starting dynamic data search...")
    
    df, metadata = fetch_from_openml(keywords)
    if df is not None:
        return df, metadata
    
    df, metadata = fetch_from_huggingface(keywords)
    if df is not None:
        return df, metadata
    
    # No real data found
    _logger.error("No valid real dataset found matching the schema.")
    
    # Check SIMULATION_MODE
    sim_mode = get_env_bool("SIMULATION_MODE", False)
    if sim_mode:
        _logger.warning("SIMULATION_MODE is True. Proceeding without real data (per T010a).")
        raise DataGapError("SIMULATION_MODE is active: No real data found, proceeding to simulation.")
    else:
        raise DataGapError("No valid real dataset found. Set SIMULATION_MODE=True to proceed or fix source.")


def validate_and_filter_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates and filters the dataset based on schema and basic rules.
    """
    required_cols = ["age", "stimulus_type", "perseverative_errors", "categories_completed"]
    
    # Check schema again
    if not _check_schema_compatibility(df, required_cols):
        _logger.error("Dataset schema validation failed.")
        raise ValueError("Dataset missing required columns.")
    
    # Basic filtering (age >= 65) is handled in T011/T012a, but we ensure types here
    df = df.copy()
    
    # Ensure numeric columns are numeric
    for col in ["age", "perseverative_errors", "categories_completed"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def save_exclusion_log(exclusion_counts: Dict[str, int], path: str) -> None:
    """
    Saves the exclusion log to a JSON file.
    """
    with open(path, 'w') as f:
        json.dump(exclusion_counts, f, indent=2)
    _logger.info(f"Saved exclusion log to {path}")


def main():
    """
    Main function to run the ingestion pipeline.
    """
    config = get_config()
    ensure_dirs()
    
    keywords = ["WCST", "cognitive", "aging", "executive function"]
    
    try:
        df, metadata = load_dataset(keywords)
        
        if df is not None:
            # Validate and filter
            df = validate_and_filter_dataset(df)
            
            # Save to processed (for demonstration, though T014a handles the final save)
            processed_path = Path(config["paths"]["processed"]) / "raw_input.csv"
            df.to_csv(processed_path, index=False)
            _logger.info(f"Saved raw input to {processed_path}")
            
            # Save metadata
            metadata_path = Path(config["paths"]["raw"]) / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            _logger.info(f"Saved metadata to {metadata_path}")
            
        else:
            _logger.critical("No data loaded.")
            
    except DataGapError as e:
        _logger.critical(str(e))
        raise
    except Exception as e:
        _logger.critical(f"Ingestion failed: {e}")
        raise


if __name__ == "__main__":
    main()