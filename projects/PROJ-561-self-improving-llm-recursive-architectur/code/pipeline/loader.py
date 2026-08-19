import time
import os
import logging
import hashlib
import requests
from functools import wraps
from typing import List, Callable, Any, Optional
from config import get_config

logger = logging.getLogger(__name__)

class HFTransientError(Exception):
    """Exception raised for transient Hugging Face errors (503, 429, timeouts)."""
    pass

def exponential_backoff(max_retries: int = 5, initial_delay: float = 2.0, backoff_factor: float = 2.0, jitter: bool = True):
    """
    Decorator that wraps a function with exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts (default 5).
        initial_delay: Initial delay in seconds (default 2.0).
        backoff_factor: Multiplier for delay after each failure (default 2.0).
        jitter: If True, adds random jitter to delay to prevent thundering herd (default True).
    
    The wrapper will retry the function on specific transient exceptions:
    - requests.exceptions.Timeout
    - requests.exceptions.ConnectionError
    - requests.exceptions.HTTPError (for 5xx and 429 status codes)
    - HFTransientError (custom exception defined here)
    
    If all retries are exhausted, the last exception is raised.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.Timeout, 
                        requests.exceptions.ConnectionError, 
                        HFTransientError) as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    # Add jitter if enabled
                    if jitter:
                        import random
                        delay_with_jitter = delay * (0.5 + random.random())
                    else:
                        delay_with_jitter = delay
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay_with_jitter:.2f}s..."
                    )
                    time.sleep(delay_with_jitter)
                    delay *= backoff_factor
                    
                except requests.exceptions.HTTPError as e:
                    # Check if it's a transient server error
                    if hasattr(e, 'response') and e.response is not None:
                        status_code = e.response.status_code
                        if status_code >= 500 or status_code == 429:
                            last_exception = e
                            if attempt == max_retries:
                                logger.error(f"Function {func.__name__} failed after {max_retries} retries with HTTP {status_code}: {e}")
                                raise
                            
                            if jitter:
                                import random
                                delay_with_jitter = delay * (0.5 + random.random())
                            else:
                                delay_with_jitter = delay
                            
                            logger.warning(
                                f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__} with HTTP {status_code}. "
                                f"Retrying in {delay_with_jitter:.2f}s..."
                            )
                            time.sleep(delay_with_jitter)
                            delay *= backoff_factor
                        else:
                            # Non-retryable HTTP error, raise immediately
                            raise
                    else:
                        # No response object, raise immediately
                        raise
                    
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
        return wrapper
    return decorator

@exponential_backoff(max_retries=5, initial_delay=2.0)
def verify_urls(urls: List[str]) -> bool:
    """
    Verifies that all provided URLs are reachable.
    
    Args:
        urls: List of URLs to verify.
        
    Returns:
        True if all URLs are reachable (200 OK).
        
    Raises:
        requests.exceptions.RequestException: If any URL is unreachable.
        ValueError: If any URL returns a non-200 status code.
    """
    for url in urls:
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code != 200:
                raise ValueError(f"URL {url} returned status code {response.status_code}")
            logger.info(f"Verified URL: {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to verify URL {url}: {e}")
            raise
    return True

@exponential_backoff(max_retries=5, initial_delay=2.0)
def download_and_checksum(dataset_name: str, dest_path: str) -> str:
    """
    Downloads a dataset file and computes its SHA-256 checksum.
    
    Args:
        dataset_name: Name of the dataset (used to construct URL or identify source).
        dest_path: Path where the file should be saved.
        
    Returns:
        The SHA-256 checksum of the downloaded file.
        
    Raises:
        requests.exceptions.RequestException: If download fails.
        FileNotFoundError: If the file cannot be written.
    """
    # Construct URL based on dataset name (simplified for this implementation)
    # In a real scenario, this would map to specific Hugging Face URLs
    base_url = "https://huggingface.co/datasets/"
    url = f"{base_url}{dataset_name}/raw/main/data.zip"  # Simplified URL construction
    
    logger.info(f"Downloading {dataset_name} from {url} to {dest_path}")
    
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()
    
    # Ensure destination directory exists
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    file_hash = hashlib.sha256()
    
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                file_hash.update(chunk)
    
    checksum = file_hash.hexdigest()
    logger.info(f"Downloaded {dataset_name} successfully. Checksum: {checksum}")
    
    # Save checksum to a separate file
    checksum_path = dest_path + ".sha256"
    with open(checksum_path, 'w') as f:
        f.write(checksum)
        
    return checksum

def load_openwebtext():
    """Load OpenWebText dataset with streaming support."""
    from datasets import load_dataset
    config = get_config()
    try:
        dataset = load_dataset("openwebtext", split="train", streaming=True)
        return dataset
    except Exception as e:
        logger.error(f"Failed to load OpenWebText: {e}")
        raise

def load_gsm8k():
    """Load GSM8K dataset with streaming support."""
    from datasets import load_dataset
    try:
        dataset = load_dataset("gsm8k", "main", split="train", streaming=True)
        return dataset
    except Exception as e:
        logger.error(f"Failed to load GSM8K: {e}")
        raise

def load_arc_challenge():
    """Load ARC-Challenge dataset with streaming support."""
    from datasets import load_dataset
    try:
        dataset = load_dataset("allenai/ai2_arc", "ARC-Challenge", split="test", streaming=True)
        return dataset
    except Exception as e:
        logger.error(f"Failed to load ARC-Challenge: {e}")
        raise

def load_boolq():
    """Load BoolQ dataset with streaming support."""
    from datasets import load_dataset
    try:
        dataset = load_dataset("boolq", split="train", streaming=True)
        return dataset
    except Exception as e:
        logger.error(f"Failed to load BoolQ: {e}")
        raise

def load_local_dataset(path: str):
    """Load a local dataset from a file."""
    from datasets import load_dataset
    try:
        if path.endswith('.json'):
            dataset = load_dataset("json", data_files=path, split="train")
        elif path.endswith('.csv'):
            dataset = load_dataset("csv", data_files=path, split="train")
        else:
            raise ValueError(f"Unsupported file format: {path}")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load local dataset {path}: {e}")
        raise

def load_all_datasets():
    """Load all required datasets."""
    datasets = {
        "openwebtext": load_openwebtext(),
        "gsm8k": load_gsm8k(),
        "arc_challenge": load_arc_challenge(),
        "boolq": load_boolq()
    }
    return datasets
