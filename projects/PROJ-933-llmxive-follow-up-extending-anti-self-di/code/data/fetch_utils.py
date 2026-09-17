import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import hashlib
import json
import requests
from datasets import load_dataset
from huggingface_hub import hf_hub_download

class DataFetchError(Exception):
    """Custom exception for data fetching failures.
    
    This exception MUST be raised when real data fetch fails.
    It is used to prevent silent fallbacks to synthetic data.
    """
    pass

def load_real_dataset(dataset_name: str, split: str = "train", streaming: bool = True) -> Any:
    """
    Load a real dataset from HuggingFace Hub.
    
    Args:
        dataset_name: Name of the dataset on HuggingFace Hub (e.g., "HuggingFaceH4/ultrafeedback")
        split: Dataset split to load (e.g., "train", "test")
        streaming: If True, stream the dataset instead of loading into memory
    
    Returns:
        Dataset or IterableDataset object from the datasets library
    
    Raises:
        DataFetchError: If the dataset cannot be fetched for any reason
    """
    try:
        # Attempt to load the dataset
        if streaming:
            dataset = load_dataset(dataset_name, split=split, streaming=True)
        else:
            dataset = load_dataset(dataset_name, split=split)
        
        # Verify we got something
        if dataset is None:
            raise DataFetchError(f"Dataset {dataset_name} returned None")
        
        # Try to peek at the data to ensure it's accessible
        if streaming:
            # For streaming datasets, try to get the first item
            first_item = next(iter(dataset))
            if first_item is None:
                raise DataFetchError(f"Dataset {dataset_name} is empty or inaccessible")
        else:
            if len(dataset) == 0:
                raise DataFetchError(f"Dataset {dataset_name} is empty")
        
        return dataset
    
    except Exception as e:
        # ALWAYS raise DataFetchError - never fallback to synthetic
        raise DataFetchError(f"Failed to fetch real dataset '{dataset_name}': {str(e)}") from e

def validate_dataset_structure(dataset: Any, required_fields: List[str]) -> bool:
    """
    Validate that a dataset contains the required fields.
    
    Args:
        dataset: Dataset object to validate
        required_fields: List of field names that must be present
    
    Returns:
        True if all required fields are present
    
    Raises:
        DataFetchError: If validation fails
    """
    try:
        # Get column names
        if hasattr(dataset, 'column_names'):
            columns = dataset.column_names
        else:
            # For streaming datasets, peek at first item
            first_item = next(iter(dataset))
            columns = list(first_item.keys())
        
        missing_fields = [field for field in required_fields if field not in columns]
        
        if missing_fields:
            raise DataFetchError(
                f"Dataset missing required fields: {missing_fields}. "
                f"Available fields: {columns}"
            )
        
        return True
    
    except DataFetchError:
        raise
    except Exception as e:
        raise DataFetchError(f"Failed to validate dataset structure: {str(e)}") from e

def compute_dataset_checksum(dataset: Any, num_samples: int = 1000) -> str:
    """
    Compute a checksum of a dataset sample for integrity verification.
    
    Args:
        dataset: Dataset to checksum
        num_samples: Number of samples to include in checksum
    
    Returns:
        Hex digest of the checksum
    
    Raises:
        DataFetchError: If checksum computation fails
    """
    try:
        hasher = hashlib.sha256()
        count = 0
        
        for item in dataset:
            if count >= num_samples:
                break
            
            # Serialize item to JSON for consistent hashing
            item_str = json.dumps(item, sort_keys=True, default=str)
            hasher.update(item_str.encode('utf-8'))
            count += 1
        
        return hasher.hexdigest()
    
    except Exception as e:
        raise DataFetchError(f"Failed to compute dataset checksum: {str(e)}") from e

def fetch_with_retry(
    url: str,
    max_retries: int = 3,
    timeout: int = 30
) -> requests.Response:
    """
    Fetch a URL with retry logic.
    
    Args:
        url: URL to fetch
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
    
    Returns:
        Response object from requests
    
    Raises:
        DataFetchError: If fetch fails after all retries
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                # Wait before retry (exponential backoff could be added)
                continue
    
    raise DataFetchError(
        f"Failed to fetch {url} after {max_retries} attempts: {str(last_exception)}"
    ) from last_exception

def download_file_to_cache(
    url: str,
    cache_dir: Optional[Path] = None,
    filename: Optional[str] = None
) -> Path:
    """
    Download a file to the cache directory.
    
    Args:
        url: URL to download from
        cache_dir: Directory to cache the file in (defaults to ~/.cache/llmxive)
        filename: Name to save the file as (defaults to URL basename)
    
    Returns:
        Path to the downloaded file
    
    Raises:
        DataFetchError: If download fails
    """
    if cache_dir is None:
        cache_dir = Path.home() / ".cache" / "llmxive"
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        filename = os.path.basename(url.split('?')[0])
    
    file_path = cache_dir / filename
    
    # Check if already downloaded
    if file_path.exists():
        return file_path
    
    try:
        response = fetch_with_retry(url)
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return file_path
    
    except DataFetchError:
        raise
    except Exception as e:
        raise DataFetchError(f"Failed to download {url}: {str(e)}") from e
