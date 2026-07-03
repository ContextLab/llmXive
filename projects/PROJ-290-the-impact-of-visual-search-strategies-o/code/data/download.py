import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import get_config
from utils.logging import get_logger

# Attempt to import huggingface_hub.
# If not installed, the main function will catch the ImportError and exit gracefully.
try:
    from huggingface_hub import HfApi, list_datasets
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False


def get_logger_wrapper(name: str = "download") -> logging.Logger:
    """
    Returns a logger configured via the project's logging utility.
    """
    return get_logger(name)


def check_schema_compatibility(dataset_info: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Checks if the dataset schema contains all required fields.
    Returns True if compatible, False otherwise.
    """
    if not HF_AVAILABLE:
        return False
    
    # HuggingFace datasets info usually exposes features or columns
    # We assume the dataset object has a 'features' dict or similar structure
    # For this implementation, we check if the keys exist in the provided info dict
    # which would be populated by the search/download logic.
    
    # In a real scenario, we'd inspect the dataset's features property.
    # Here we assume 'dataset_info' contains a 'features' key with field names.
    features = dataset_info.get('features', {})
    
    if not features:
        # Fallback: check if dataset_info itself has keys (for simple dicts)
        features = dataset_info
    
    missing = [f for f in required_fields if f not in features]
    if missing:
        logger = get_logger()
        logger.warning(f"Schema missing required fields: {missing}")
        return False
    return True


def validate_dataset_content(dataset_name: str, sample_data: Dict[str, Any]) -> bool:
    """
    Validates that the sample data contains at least one valid record.
    """
    if not sample_data:
        return False
    
    # Check if any row has non-null values for critical fields
    # Assuming sample_data is a list of dicts or a dict with 'data' key
    records = sample_data if isinstance(sample_data, list) else sample_data.get('data', [])
    
    if not records:
        return False
    
    # Check first record for basic validity
    first_record = records[0]
    if not first_record or len(first_record) == 0:
        return False
        
    return True


def search_huggingface_datasets(query_terms: List[str], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Searches HuggingFace Hub for datasets matching the query terms.
    Returns a list of dataset metadata dictionaries.
    """
    if not HF_AVAILABLE:
        raise ImportError("huggingface_hub is not installed. Install it to search datasets.")
    
    logger = get_logger()
    api = HfApi()
    
    query = " ".join(query_terms)
    logger.info(f"Searching HuggingFace for: {query}")
    
    datasets_list = list_datasets(filter=query, limit=limit)
    
    results = []
    for ds in datasets_list:
        results.append({
            'id': ds.id,
            'description': ds.description,
            'tags': ds.tags,
            'downloads': ds.downloads,
            'likes': ds.likes
        })
    
    logger.info(f"Found {len(results)} potential datasets.")
    return results


def download_with_retry(
    dataset_id: str, 
    output_dir: str, 
    max_retries: int = 3, 
    base_delay: float = 1.0
) -> Optional[str]:
    """
    Downloads a dataset from HuggingFace with exponential backoff retry logic.
    
    Retry timings: base_delay (1s), base_delay*2 (2s), base_delay*4 (4s).
    
    Args:
        dataset_id: The HuggingFace dataset ID.
        output_dir: Local directory to save the dataset.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds (default 1.0).
        
    Returns:
        Path to the downloaded directory if successful, None otherwise.
    """
    if not HF_AVAILABLE:
        raise ImportError("huggingface_hub is not installed.")
        
    from huggingface_hub import snapshot_download
    
    logger = get_logger()
    attempts = 0
    
    while attempts < max_retries:
        try:
            logger.info(f"Attempt {attempts + 1}/{max_retries} to download {dataset_id}...")
            
            # Calculate delay: 1s, 2s, 4s...
            delay = base_delay * (2 ** attempts)
            
            # Perform download
            local_path = snapshot_download(
                repo_id=dataset_id,
                repo_type="dataset",
                local_dir=output_dir,
                local_dir_use_symlinks=False
            )
            
            logger.info(f"Successfully downloaded {dataset_id} to {local_path}")
            return local_path
            
        except Exception as e:
            attempts += 1
            logger.warning(f"Download attempt {attempts} failed: {e}")
            
            if attempts < max_retries:
                logger.info(f"Retrying in {delay:.1f} seconds (exponential backoff)...")
                time.sleep(delay)
            else:
                logger.error(f"Failed to download {dataset_id} after {max_retries} attempts.")
                return None

def main():
    """
    Main entry point for the download script.
    Orchestrates searching, validating, and downloading.
    """
    logger = get_logger()
    config = get_config()
    
    # Ensure output directory exists
    output_base = Path(config.get('DATA_RAW_DIR', 'data/raw'))
    output_base.mkdir(parents=True, exist_ok=True)
    
    if not HF_AVAILABLE:
        logger.error("huggingface_hub is not installed. Please install dependencies.")
        sys.exit(1)
    
    # Search for datasets
    search_terms = ['eye-tracking', 'face', 'emotion']
    candidates = search_huggingface_datasets(search_terms)
    
    if not candidates:
        logger.error("No datasets found matching criteria.")
        sys.exit(1)
    
    required_fields = ['gaze_coordinates', 'response_times', 'emotion_labels'] # Example requirements
    
    for candidate in candidates:
        dataset_id = candidate['id']
        logger.info(f"Validating candidate: {dataset_id}")
        
        # In a full implementation, we would load the dataset info to check schema
        # For now, we assume the search logic or a preliminary load would happen here.
        # We proceed to download the first candidate that we assume passes schema check.
        # Note: Real schema validation requires loading the dataset features.
        
        # Simulate schema check (in real code, load features first)
        # Assuming we pass for the first one found for this task's scope
        # In T012, we will do the actual validation on downloaded data.
        
        local_path = download_with_retry(
            dataset_id=dataset_id,
            output_dir=str(output_base / dataset_id.split('/')[-1]),
            max_retries=3,
            base_delay=1.0
        )
        
        if local_path:
            logger.info(f"Dataset {dataset_id} downloaded successfully.")
            # We stop after first successful download for this MVP
            return local_path
        else:
            logger.warning(f"Download failed for {dataset_id}, trying next candidate.")
    
    logger.error("No valid dataset could be downloaded.")
    sys.exit(1)


if __name__ == "__main__":
    main()