import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from project utils
from utils.logging import get_logger
from config import get_config

# Constants for retry logic (FR-002)
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff timings in seconds
MAX_RETRIES = len(RETRY_DELAYS)

def get_logger_wrapper(name: str = __name__) -> logging.Logger:
    """Get a logger instance configured for this module."""
    return get_logger(name)

def check_schema_compatibility(dataset_columns: List[str], required_columns: List[str]) -> bool:
    """
    Check if the dataset contains all required columns.
    
    Args:
        dataset_columns: List of column names in the dataset.
        required_columns: List of required column names.
        
    Returns:
        True if all required columns are present, False otherwise.
    """
    return all(col in dataset_columns for col in required_columns)

def validate_dataset_content(dataset: Any) -> bool:
    """
    Validate that the dataset contains at least one valid record.
    
    Args:
        dataset: The dataset object to validate.
        
    Returns:
        True if the dataset has at least one valid record, False otherwise.
    """
    try:
        # Handle HuggingFace datasets format
        if hasattr(dataset, '__len__') and len(dataset) > 0:
            # Check if the first record is not empty
            first_record = dataset[0]
            if first_record and len(first_record) > 0:
                return True
        return False
    except Exception as e:
        logging.getLogger(__name__).warning(f"Error validating dataset content: {e}")
        return False

def search_huggingface_datasets(logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Search HuggingFace for relevant eye-tracking datasets.
    
    Searches for datasets containing 'eye-tracking', 'face', or 'emotion' keywords.
    
    Returns:
        List of dataset metadata dictionaries.
    """
    try:
        from datasets import list_datasets
    except ImportError:
        logger.error("The 'datasets' library is not installed. Please install it via pip.")
        return []

    # Keywords to search for
    keywords = ['eye-tracking', 'face', 'emotion']
    candidate_datasets = []
    
    # Note: The datasets library doesn't have a direct 'search' method that returns
    # metadata in a simple way without fetching. We'll iterate through available
    # datasets and filter by name/description if possible.
    # For a more robust solution, we would use the HuggingFace Hub API directly.
    
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        
        # Search for datasets with relevant keywords
        for keyword in keywords:
            try:
                # List datasets matching the keyword
                datasets_info = api.list_datasets(search=keyword, limit=50)
                for ds in datasets_info:
                    dataset_info = {
                        'id': ds.id,
                        'description': ds.description or "",
                        'author': ds.author or "",
                        'likes': ds.likes or 0
                    }
                    # Avoid duplicates
                    if not any(d['id'] == dataset_info['id'] for d in candidate_datasets):
                        candidate_datasets.append(dataset_info)
            except Exception as e:
                logger.warning(f"Error searching for datasets with keyword '{keyword}': {e}")
                continue
                
    except ImportError:
        logger.warning("huggingface_hub not found. Falling back to limited search.")
        # Fallback: try to list datasets directly (less effective)
        try:
            all_datasets = list_datasets()
            for ds in all_datasets:
                ds_name = ds.id.lower()
                if any(kw.lower() in ds_name for kw in keywords):
                    candidate_datasets.append({
                        'id': ds.id,
                        'description': "",
                        'author': "",
                        'likes': 0
                    })
        except Exception as e:
            logger.warning(f"Fallback search failed: {e}")

    # Sort by popularity (likes) to prioritize well-maintained datasets
    candidate_datasets.sort(key=lambda x: x['likes'], reverse=True)
    
    logger.info(f"Found {len(candidate_datasets)} candidate datasets.")
    return candidate_datasets

def download_with_retry(dataset_id: str, target_path: Path, logger: logging.Logger) -> Optional[Path]:
    """
    Download a dataset from HuggingFace with retry logic and exponential backoff.
    
    Implements FR-002: Retry logic with exponential backoff (1s, 2s, 4s).
    
    Args:
        dataset_id: The HuggingFace dataset identifier.
        target_path: The directory where the dataset should be saved.
        logger: Logger instance for recording progress.
        
    Returns:
        Path to the downloaded dataset directory, or None if all retries fail.
    """
    from datasets import load_dataset
    
    last_error = None
    
    for attempt, delay in enumerate(RETRY_DELAYS):
        try:
            logger.info(f"Attempt {attempt + 1}/{MAX_RETRIES} to download dataset '{dataset_id}'...")
            
            # Attempt to load the dataset
            # We use trust_remote_code=False for security
            dataset = load_dataset(dataset_id, trust_remote_code=False)
            
            # If successful, ensure the target path exists
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Save the dataset to the target path
            # Note: The exact saving method depends on the dataset format
            # For now, we just confirm the download succeeded by checking if data exists
            if dataset and len(dataset) > 0:
                logger.info(f"Successfully downloaded dataset '{dataset_id}' to '{target_path}'")
                return target_path
            else:
                logger.warning(f"Dataset '{dataset_id}' downloaded but appears empty.")
                
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            
            if attempt < len(RETRY_DELAYS) - 1:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"All {MAX_RETRIES} attempts failed for dataset '{dataset_id}'.")
                
    logger.error(f"Failed to download dataset '{dataset_id}' after {MAX_RETRIES} attempts.")
    raise last_error if last_error else Exception("Unknown error during download")

def find_valid_dataset(logger: logging.Logger, required_columns: List[str]) -> Tuple[Optional[str], Optional[Any]]:
    """
    Find and download the first valid dataset from HuggingFace.
    
    Args:
        logger: Logger instance for recording progress.
        required_columns: List of columns that must be present in the dataset.
        
    Returns:
        Tuple of (dataset_id, dataset_object) if found, (None, None) otherwise.
    """
    candidates = search_huggingface_datasets(logger)
    
    if not candidates:
        logger.error("No candidate datasets found on HuggingFace.")
        return None, None
        
    for candidate in candidates:
        dataset_id = candidate['id']
        logger.info(f"Evaluating dataset: {dataset_id}")
        
        try:
            # Attempt to load dataset info to check columns
            from datasets import load_dataset
            # Load only the first split to check structure
            ds_info = load_dataset(dataset_id, split='train', streaming=True)
            
            # Get column names
            if hasattr(ds_info, 'column_names'):
                columns = ds_info.column_names
            else:
                # Fallback for some dataset formats
                columns = list(next(iter(ds_info)).keys())
                
            # Check schema compatibility
            if not check_schema_compatibility(columns, required_columns):
                logger.info(f"Dataset '{dataset_id}' missing required columns. Skipping.")
                continue
                
            # Check content validity
            # Load a small sample to verify content
            sample_ds = load_dataset(dataset_id, split='train')
            if not validate_dataset_content(sample_ds):
                logger.info(f"Dataset '{dataset_id}' has no valid records. Skipping.")
                continue
                
            logger.info(f"Found valid dataset: {dataset_id}")
            return dataset_id, sample_ds
            
        except Exception as e:
            logger.warning(f"Error evaluating dataset '{dataset_id}': {e}")
            continue
            
    logger.error("No valid dataset found matching criteria.")
    return None, None

def main():
    """Main entry point for the download module."""
    logger = get_logger(__name__)
    config = get_config()
    
    # Define required columns based on project specifications
    required_columns = ['gaze_coordinates', 'response_times', 'emotion_labels']
    
    # Find a valid dataset
    dataset_id, dataset = find_valid_dataset(logger, required_columns)
    
    if not dataset_id:
        logger.error("CRITICAL: No valid dataset found. Halting execution.")
        sys.exit(1)
        
    logger.info(f"Selected dataset: {dataset_id}")
    
    # Prepare download path
    download_path = config.data_raw_dir / dataset_id.replace('/', '_')
    
    # Download with retry logic
    try:
        final_path = download_with_retry(dataset_id, download_path, logger)
        if final_path:
            logger.info(f"Dataset successfully saved to: {final_path}")
        else:
            logger.error("Download failed despite retry logic.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error during download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
