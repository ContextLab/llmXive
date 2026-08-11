import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd
import openml
from datasets import load_dataset

from utils import setup_logging, log_info, log_warning, log_error, compute_sha256
from config import get_config, ensure_dirs

logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass

class DataGapError(Exception):
    """Raised when a required data gap is detected (e.g., no matching dataset)."""
    pass

def fetch_from_openml(keywords: List[str], max_datasets: int = 50) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Search OpenML for datasets matching keywords and fetch the first valid one.
    
    Args:
        keywords: List of keywords to search (e.g., "WCST", "cognitive", "aging").
        max_datasets: Maximum number of datasets to scan.
        
    Returns:
        Tuple of (DataFrame, dataset_source_string) or (None, None) if not found.
    """
    log_info(f"Searching OpenML for datasets with keywords: {keywords}")
    
    # Build search query
    search_query = " OR ".join(keywords)
    
    try:
        # List datasets (OpenML API)
        datasets = openml.datasets.list_datasets(search=search_query, output_format="dataframe")
        
        if datasets is None or datasets.empty:
            log_warning(f"No OpenML datasets found for query: {search_query}")
            return None, None
        
        # Limit to max_datasets
        datasets = datasets.head(max_datasets)
        
        for _, row in datasets.iterrows():
            dataset_id = row['did']
            dataset_name = row['name']
            log_info(f"Checking dataset ID {dataset_id}: {dataset_name}")
            
            try:
                # Fetch dataset
                openml_dataset = openml.datasets.get_dataset(dataset_id)
                df, _, _, _ = openml_dataset.get_data()
                
                # Validate schema
                required_cols = {'age', 'stimulus_type', 'perseverative_errors', 'categories_completed'}
                available_cols = set(df.columns)
                
                if required_cols.issubset(available_cols):
                    log_info(f"Found valid dataset: {dataset_name} (ID: {dataset_id})")
                    return df, f"OpenML:{dataset_id}:{dataset_name}"
                else:
                    missing = required_cols - available_cols
                    log_debug(f"Dataset {dataset_name} missing columns: {missing}")
                    
            except Exception as e:
                log_warning(f"Failed to fetch or validate dataset {dataset_id}: {e}")
                continue
                
    except Exception as e:
        log_error(f"Error searching OpenML: {e}")
        return None, None
        
    return None, None

def fetch_from_huggingface(keywords: List[str]) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Search HuggingFace for datasets matching keywords and fetch the first valid one.
    
    Args:
        keywords: List of keywords to search.
        
    Returns:
        Tuple of (DataFrame, dataset_source_string) or (None, None) if not found.
    """
    log_info(f"Searching HuggingFace for datasets with keywords: {keywords}")
    
    # HuggingFace list_datasets doesn't support keyword search directly in the same way,
    # so we try common dataset IDs or names related to the keywords
    candidate_ids = []
    for kw in keywords:
        candidate_ids.extend([
            kw.lower().replace(" ", "_"),
            f"{kw.lower()}_dataset",
            f"{kw.lower()}_data",
            f"aging_{kw.lower()}",
            f"wcst_data"
        ])
    
    # Remove duplicates
    candidate_ids = list(set(candidate_ids))
    
    for dataset_id in candidate_ids[:20]:  # Limit attempts
        try:
            log_info(f"Attempting to load HuggingFace dataset: {dataset_id}")
            ds = load_dataset(dataset_id, split="train")
            df = ds.to_pandas()
            
            # Validate schema
            required_cols = {'age', 'stimulus_type', 'perseverative_errors', 'categories_completed'}
            available_cols = set(df.columns)
            
            if required_cols.issubset(available_cols):
                log_info(f"Found valid dataset: {dataset_id}")
                return df, f"HuggingFace:{dataset_id}"
            else:
                missing = required_cols - available_cols
                log_debug(f"Dataset {dataset_id} missing columns: {missing}")
                
        except Exception as e:
            # Dataset not found or invalid
            continue
            
    return None, None

def fetch_from_url(url: str) -> pd.DataFrame:
    """Fetch data from a URL (CSV/JSON)."""
    log_info(f"Fetching data from URL: {url}")
    try:
        if url.endswith('.csv'):
            return pd.read_csv(url)
        elif url.endswith('.json'):
            return pd.read_json(url)
        else:
            raise DataFetchError(f"Unsupported file format: {url}")
    except Exception as e:
        raise DataFetchError(f"Failed to fetch from URL {url}: {e}")

def fetch_metadata_from_source(source: str) -> Dict[str, Any]:
    """Fetch metadata from the source (OpenML/HF)."""
    # Placeholder for metadata extraction
    return {
        "source": source,
        "timestamp": pd.Timestamp.now().isoformat()
    }

def load_local_file(path: str) -> pd.DataFrame:
    """Load a local CSV file."""
    return pd.read_csv(path)

def generate_synthetic_fallback(seed: int = 42, n_samples: int = 200) -> pd.DataFrame:
    """
    Generate a deterministic synthetic dataset for pipeline validation.
    ONLY used if NO real dataset is found.
    """
    log_warning("No real dataset found. Generating deterministic synthetic fallback.")
    
    import numpy as np
    np.random.seed(seed)
    
    n_nostalgia = n_samples // 2
    n_control = n_samples - n_nostalgia
    
    # Generate ages >= 65
    ages = np.concatenate([
        np.random.normal(72, 6, n_nostalgia),
        np.random.normal(71, 7, n_control)
    ]).astype(int)
    ages = np.clip(ages, 65, 95)
    
    # Stimulus types
    stimulus_types = ['nostalgia'] * n_nostalgia + ['control'] * n_control
    
    # Perseverative errors (higher in control group typically)
    pe_nostalgia = np.random.normal(4.5, 1.5, n_nostalgia)
    pe_control = np.random.normal(6.0, 1.8, n_control)
    perseverative_errors = np.clip(np.concatenate([pe_nostalgia, pe_control]), 0, 15).astype(int)
    
    # Categories completed
    cc_nostalgia = np.random.normal(5.5, 0.8, n_nostalgia)
    cc_control = np.random.normal(4.5, 1.0, n_control)
    categories_completed = np.clip(np.concatenate([cc_nostalgia, cc_control]), 1, 6).astype(int)
    
    # MMSE (optional, some missing)
    mmse = np.random.normal(28, 2, n_samples).astype(int)
    mmse = np.clip(mmse, 15, 30)
    # Simulate some missing (10%)
    missing_mask = np.random.random(n_samples) < 0.1
    mmse[missing_mask] = np.nan
    
    df = pd.DataFrame({
        'participant_id': [f"P{i:04d}" for i in range(n_samples)],
        'age': ages,
        'stimulus_type': stimulus_types,
        'perseverative_errors': perseverative_errors,
        'categories_completed': categories_completed,
        'MMSE': mmse
    })
    
    return df

def fetch_data(keywords: Optional[List[str]] = None) -> Tuple[pd.DataFrame, str, bool]:
    """
    Main entry point to fetch data.
    
    Returns:
        Tuple of (DataFrame, source_string, simulation_mode)
    """
    if keywords is None:
        keywords = ["WCST", "cognitive", "aging", "executive function"]
    
    # Try OpenML first
    df, source = fetch_from_openml(keywords)
    if df is not None:
        return df, source, False
    
    # Try HuggingFace
    df, source = fetch_from_huggingface(keywords)
    if df is not None:
        return df, source, False
    
    # No real data found -> Generate synthetic fallback
    log_warning("No valid real dataset found in OpenML or HuggingFace.")
    log_warning("Generating deterministic synthetic dataset for pipeline validation.")
    
    df = generate_synthetic_fallback(seed=42, n_samples=200)
    source = "SYNTHETIC:FALLBACK:seed42"
    
    return df, source, True

def fetch_metadata_from_url(url: str) -> Dict[str, Any]:
    """Fetch metadata from a URL."""
    return {"source": url, "fetched": True}

def save_exclusion_log(exclusion_counts: Dict[str, int], path: str) -> None:
    """Save exclusion log to JSON."""
    with open(path, 'w') as f:
        json.dump(exclusion_counts, f, indent=2)

def save_metadata(metadata: Dict[str, Any], path: str) -> None:
    """Save metadata to JSON."""
    with open(path, 'w') as f:
        json.dump(metadata, f, indent=2)