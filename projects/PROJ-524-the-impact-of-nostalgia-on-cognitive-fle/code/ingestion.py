import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

# Import from utils and config as per API surface
from utils import setup_logging, log_info, log_warning, log_error, compute_sha256
from config import get_config, ensure_dirs, get_data_source_url, get_log_level

# Constants
LOG = logging.getLogger(__name__)

def fetch_metadata_from_source(source_type: str, source_id: str) -> Dict[str, Any]:
    """
    Fetch metadata from a specified source (openml, huggingface, local).
    This is a stub implementation for T013b context; real implementation
    would call specific APIs.
    """
    LOG.info(f"Fetching metadata from {source_type}: {source_id}")
    # Placeholder logic - in a real scenario, this would fetch from API
    return {"source": source_type, "id": source_id, "columns": []}

def load_local_file(file_path: str) -> Tuple[Any, Dict[str, Any]]:
    """
    Load a local dataset file (CSV, JSON, etc.) and return data + metadata.
    Returns (dataframe, metadata_dict).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    LOG.info(f"Loading local file: {file_path}")
    
    # Simple CSV loading for demonstration
    if path.suffix == '.csv':
        import pandas as pd
        df = pd.read_csv(path)
        columns = list(df.columns)
        metadata = {
            "source": "local",
            "path": str(path),
            "columns": columns,
            "row_count": len(df)
        }
        return df, metadata
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def fetch_from_openml(dataset_id: int) -> Tuple[Any, Dict[str, Any]]:
    """
    Fetch dataset from OpenML.
    """
    LOG.info(f"Fetching from OpenML: {dataset_id}")
    try:
        import openml
        dataset = openml.datasets.get_dataset(dataset_id)
        df, _, _, _ = dataset.get_data()
        columns = list(df.columns)
        metadata = {
            "source": "openml",
            "id": dataset_id,
            "columns": columns,
            "row_count": len(df)
        }
        return df, metadata
    except Exception as e:
        log_error(f"Failed to fetch from OpenML: {e}")
        raise

def fetch_from_huggingface(dataset_name: str) -> Tuple[Any, Dict[str, Any]]:
    """
    Fetch dataset from HuggingFace Datasets.
    """
    LOG.info(f"Fetching from HuggingFace: {dataset_name}")
    try:
        from datasets import load_dataset
        ds = load_dataset(dataset_name, split="train")
        df = ds.to_pandas()
        columns = list(df.columns)
        metadata = {
            "source": "huggingface",
            "name": dataset_name,
            "columns": columns,
            "row_count": len(df)
        }
        return df, metadata
    except Exception as e:
        log_error(f"Failed to fetch from HuggingFace: {e}")
        raise

def fetch_from_url(url: str) -> Tuple[Any, Dict[str, Any]]:
    """
    Fetch dataset from a direct URL.
    """
    LOG.info(f"Fetching from URL: {url}")
    import requests
    import pandas as pd
    from io import StringIO

    response = requests.get(url)
    response.raise_for_status()
    
    # Assume CSV for now
    df = pd.read_csv(StringIO(response.text))
    columns = list(df.columns)
    metadata = {
        "source": "url",
        "url": url,
        "columns": columns,
        "row_count": len(df)
    }
    return df, metadata

def fetch_metadata_from_url(url: str) -> Dict[str, Any]:
    """
    Fetch metadata from a URL (e.g., metadata.json).
    """
    LOG.info(f"Fetching metadata from URL: {url}")
    import requests
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def load_dataset(source_type: str, source_id: str, local_path: Optional[str] = None) -> Tuple[Any, Dict[str, Any]]:
    """
    Main loader function that dispatches to specific fetchers.
    """
    if source_type == "local":
        if not local_path:
            raise ValueError("local_path required for local source")
        return load_local_file(local_path)
    elif source_type == "openml":
        return fetch_from_openml(int(source_id))
    elif source_type == "huggingface":
        return fetch_from_huggingface(source_id)
    elif source_type == "url":
        return fetch_from_url(source_id)
    else:
        raise ValueError(f"Unknown source type: {source_type}")

def validate_and_filter_dataset(df: Any, metadata: Dict[str, Any], config: Dict[str, Any]) -> Tuple[Any, List[Dict[str, Any]]]:
    """
    Validate and filter the dataset based on age >= 65 and other criteria.
    Returns (filtered_df, exclusion_log_list).
    """
    LOG.info("Validating and filtering dataset")
    import pandas as pd

    exclusion_log = []
    
    # Check for MMSE column presence (Task T013b)
    columns = df.columns.tolist()
    has_mmse = 'MMSE' in columns
    
    # Update config with MMSE flag
    config['has_mmse'] = has_mmse
    
    if not has_mmse:
        log_warning("ERR_MMSE_MISSING: 'MMSE' column not found in raw dataset.")
        # Log the warning event
        exclusion_log.append({
            "type": "ERR_MMSE_MISSING",
            "message": "MMSE column not found",
            "count": 0
        })
    else:
        log_info("MMSE column found in dataset.")

    # Filter by age >= 65
    if 'age' in columns:
        initial_count = len(df)
        df = df[df['age'] >= 65].copy()
        filtered_count = len(df)
        if initial_count != filtered_count:
            exclusion_log.append({
                "type": "ERR_AGE_FILTER",
                "message": f"Filtered records with age < 65",
                "count": initial_count - filtered_count
            })
    else:
        log_error("ERR_MISSING_AGE_FIELD: 'age' column not found.")
        exclusion_log.append({
            "type": "ERR_MISSING_AGE_FIELD",
            "message": "Age column missing",
            "count": len(df)
        })
        return pd.DataFrame(), exclusion_log

    return df, exclusion_log

def save_exclusion_log(exclusion_log: List[Dict[str, Any]], output_path: str):
    """
    Save the exclusion log to a JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    log_info(f"Exclusion log saved to {output_path}")

def main():
    """
    Main entry point for the ingestion script.
    """
    setup_logging()
    config = get_config()
    ensure_dirs()

    source_type = config.get('source_type', 'local')
    source_id = config.get('source_id', 'dataset_id')
    local_path = config.get('local_path', None)

    try:
        df, metadata = load_dataset(source_type, source_id, local_path)
        log_info(f"Loaded dataset with {len(df)} rows and columns: {list(df.columns)}")

        # Validate and filter (includes T013b MMSE check)
        filtered_df, exclusion_log = validate_and_filter_dataset(df, metadata, config)
        
        # Save exclusion log
        exclusion_path = config.get('exclusion_log_path', 'data/processed/exclusion_log.json')
        save_exclusion_log(exclusion_log, exclusion_path)

        log_info(f"Validation complete. Valid records: {len(filtered_df)}")
        return filtered_df, config

    except Exception as e:
        log_error(f"Ingestion failed: {e}")
        raise

if __name__ == "__main__":
    main()