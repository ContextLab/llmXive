"""
Ingestion module for the Nostalgia and Cognitive Flexibility project.
Handles fetching, validating, and cleaning data from external sources.
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd
from datasets import load_dataset
import openml
import requests

from utils import setup_logging, log_info, log_warning, log_error, compute_sha256
from config import load_config, get_config, get_env_bool, get_data_source_url

# Setup logging
logger = setup_logging("ingestion")

# Custom Exceptions
class DataFetchError(Exception):
    """Raised when data fetching from a real source fails."""
    pass

class DataGapError(Exception):
    """Raised when no valid real dataset is found and simulation is not explicitly enabled."""
    pass

class SchemaValidationError(Exception):
    """Raised when data schema does not match requirements."""
    pass

# Constants
REQUIRED_COLUMNS = ['age', 'stimulus_type', 'perseverative_errors', 'categories_completed']
MMSE_COLUMN = 'MMSE'
SIMULATION_MODE_VAR = 'SIMULATION_MODE'

def fetch_from_openml(keywords: List[str]) -> Optional[pd.DataFrame]:
    """
    Dynamically search OpenML for datasets matching keywords.
    Returns the first valid DataFrame found or None.
    """
    logger.info(f"Searching OpenML for keywords: {keywords}")
    try:
        # OpenML list_datasets is the correct API for dynamic search
        datasets = openml.datasets.list_datasets(output_format="dataframe")
        
        # Filter by keywords in name or description
        matches = datasets[datasets['name'].str.lower().str.contains('|'.join(keywords), na=False) |
                           datasets['description'].str.lower().str.contains('|'.join(keywords), na=False)]
        
        if matches.empty:
            logger.warning("No matching datasets found on OpenML.")
            return None

        # Iterate through matches to find one with required schema
        for _, row in matches.iterrows():
            dataset_id = row['did']
            try:
                logger.info(f"Attempting to fetch OpenML dataset ID: {dataset_id}")
                openml_dataset = openml.datasets.get_dataset(dataset_id)
                data, _, _, _ = openml_dataset.get_data(dataset_format="dataframe")
                
                # Check schema
                if all(col in data.columns for col in REQUIRED_COLUMNS):
                    log_info(f"Successfully fetched and validated dataset from OpenML ID {dataset_id}")
                    return data
                else:
                    logger.debug(f"Dataset {dataset_id} missing required columns. Skipping.")
            except Exception as e:
                logger.warning(f"Failed to fetch or validate OpenML dataset {dataset_id}: {e}")
                continue
        
        logger.warning("No valid datasets found on OpenML with required schema.")
        return None
    except Exception as e:
        log_error(f"Error searching OpenML: {e}")
        return None

def fetch_from_huggingface(keywords: List[str]) -> Optional[pd.DataFrame]:
    """
    Dynamically search HuggingFace for datasets matching keywords.
    Returns the first valid DataFrame found or None.
    """
    logger.info(f"Searching HuggingFace for keywords: {keywords}")
    try:
        # Note: HuggingFace Hub API for listing datasets is limited in client library.
        # We will try a few known dataset names or use the search endpoint if available.
        # For robustness, we attempt to load a specific known dataset if keywords match,
        # otherwise we rely on the user providing a path or URL.
        
        # Attempting to use the datasets library's list_datasets is not directly supported
        # for arbitrary keyword search in the same way as OpenML.
        # We will try to fetch a specific dataset if the project config specifies one,
        # or try a common dataset ID related to cognitive testing.
        
        # Fallback strategy: Try a known dataset ID if keywords match 'WCST' or 'cognitive'
        candidate_ids = [
            "mlmorg/wcst", # Hypothetical or real ID if exists
            "nlp4psych/WCST" # Example
        ]
        
        # Since dynamic keyword search on HF is complex without a direct API endpoint 
        # exposed in the standard client for arbitrary filtering, we will try 
        # to fetch based on a config-provided ID or a hardcoded list if keywords match.
        
        if any(kw.lower() in ['wcst', 'cognitive', 'aging'] for kw in keywords):
            for ds_id in candidate_ids:
                try:
                    logger.info(f"Attempting to fetch HuggingFace dataset: {ds_id}")
                    ds = load_dataset(ds_id, split="train")
                    df = ds.to_pandas()
                    if all(col in df.columns for col in REQUIRED_COLUMNS):
                        log_info(f"Successfully fetched and validated dataset from HuggingFace: {ds_id}")
                        return df
                except Exception as e:
                    logger.debug(f"Failed to fetch HF dataset {ds_id}: {e}")
                    continue
        
        logger.warning("No valid datasets found on HuggingFace with required schema.")
        return None
    except Exception as e:
        log_error(f"Error searching HuggingFace: {e}")
        return None

def fetch_from_url(url: str) -> Optional[pd.DataFrame]:
    """Fetch data from a direct URL (CSV/JSON)."""
    logger.info(f"Fetching data from URL: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        if url.endswith('.csv'):
            return pd.read_csv(pd.io.common.StringIO(response.text))
        elif url.endswith('.json'):
            return pd.read_json(pd.io.common.StringIO(response.text))
        else:
            raise ValueError(f"Unsupported file format from URL: {url}")
    except Exception as e:
        log_error(f"Failed to fetch from URL {url}: {e}")
        return None

def load_local_file(path: str) -> Optional[pd.DataFrame]:
    """Load data from a local file."""
    p = Path(path)
    if not p.exists():
        log_error(f"Local file not found: {path}")
        return None
    
    try:
        if p.suffix == '.csv':
            return pd.read_csv(p)
        elif p.suffix == '.json':
            return pd.read_json(p)
        else:
            raise ValueError(f"Unsupported file format: {path}")
    except Exception as e:
        log_error(f"Failed to load local file {path}: {e}")
        return None

def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validates that the DataFrame contains all required columns.
    Returns (is_valid, list_of_missing_columns).
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        return False, missing
    return True, []

def fetch_metadata_from_source(source_type: str, source_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch metadata about the dataset source.
    """
    metadata = {
        "dataset_source": source_type,
        "validation_study_doi": None,
        "fetched_at": str(pd.Timestamp.now())
    }
    
    if source_type == "openml" and source_id:
        try:
            ds = openml.datasets.get_dataset(int(source_id))
            metadata["validation_study_doi"] = ds.description.get('citation', {}).get('doi')
            metadata["original_name"] = ds.name
        except Exception as e:
            log_warning(f"Could not fetch metadata from OpenML: {e}")
    
    return metadata

def fetch_data(force_simulation: bool = False) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Main entry point for data fetching.
    
    Strategy:
    1. Check for local file (config).
    2. Try OpenML search.
    3. Try HuggingFace search.
    4. If all fail:
       - If force_simulation is True (SIMULATION_MODE set), raise DataGapError to allow simulation path.
       - If force_simulation is False, raise DataFetchError immediately.
    
    This task (T039) ensures NO synthetic fallback is used.
    """
    config = load_config()
    keywords = ["WCST", "cognitive", "aging", "executive function"]
    
    # 1. Check Local
    local_path = get_config().get('local_data_path')
    if local_path:
        df = load_local_file(local_path)
        if df is not None:
            is_valid, missing = validate_schema(df)
            if is_valid:
                log_info("Loaded data from local file.")
                return df, fetch_metadata_from_source("local", local_path)
            else:
                log_warning(f"Local file missing columns: {missing}")
    
    # 2. OpenML
    df = fetch_from_openml(keywords)
    if df is not None:
        # Infer ID from context or just return
        return df, fetch_metadata_from_source("openml", "dynamic_search")
    
    # 3. HuggingFace
    df = fetch_from_huggingface(keywords)
    if df is not None:
        return df, fetch_metadata_from_source("huggingface", "dynamic_search")
    
    # 4. Failure Handling (T039 Logic)
    log_error("Failed to fetch real data from any source (OpenML, HuggingFace, Local).")
    
    if force_simulation:
        log_warning("SIMULATION_MODE is active. Raising DataGapError to halt real fetch and proceed to simulation logic if handled upstream.")
        raise DataGapError("No real data found. Simulation mode requested.")
    else:
        log_critical("SIMULATION_MODE is NOT active. Halting execution due to missing real data.")
        raise DataFetchError("Failed to fetch real data. No real source available and simulation not explicitly enabled.")

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Basic cleaning: drop rows with missing required columns.
    """
    initial_count = len(df)
    df_clean = df.dropna(subset=REQUIRED_COLUMNS)
    dropped = initial_count - len(df_clean)
    if dropped > 0:
        log_info(f"Dropped {dropped} rows due to missing required columns.")
    return df_clean

def main():
    """
    Entry point for the ingestion script.
    Writes the cleaned dataset to data/processed/cleaned_dataset.csv
    """
    # Ensure directories exist
    from config import ensure_dirs
    ensure_dirs()
    
    # Check for simulation mode flag
    sim_mode = get_env_bool(SIMULATION_MODE_VAR, default=False)
    
    try:
        df, metadata = fetch_data(force_simulation=sim_mode)
        
        # Validate and clean
        df = clean_data(df)
        
        # Save raw metadata
        meta_path = Path("data/raw/metadata.json")
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        log_info(f"Saved metadata to {meta_path}")
        
        # Save cleaned dataset
        output_path = Path("data/processed/cleaned_dataset.csv")
        df.to_csv(output_path, index=False)
        log_info(f"Saved cleaned dataset to {output_path}")
        
        return df
        
    except DataGapError as e:
        log_info(f"DataGapError caught: {e}. Simulation path may follow if implemented.")
        return None
    except DataFetchError as e:
        log_critical(f"DataFetchError: {e}")
        raise
    except Exception as e:
        log_critical(f"Unexpected error during ingestion: {e}")
        raise

if __name__ == "__main__":
    main()