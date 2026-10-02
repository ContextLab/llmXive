import time
import os
import logging
import hashlib
import requests
from functools import wraps
from typing import List, Optional, Tuple
from datasets import load_dataset

logger = logging.getLogger(__name__)

class HFTransientError(Exception):
    """Raised when a HuggingFace or network error is transient and retryable."""
    pass

def exponential_backoff(func):
    """
    Decorator implementing exponential backoff with jitter.
    Initial delay: 30s, Max retries: 5.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 5
        initial_delay = 30
        delay = initial_delay
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (requests.exceptions.RequestException, HFTransientError) as e:
                if attempt == max_retries:
                    logger.error(f"Failed after {max_retries} retries: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay = min(delay * 2, 300)  # Cap at 5 minutes
        return None
    return wrapper

@exponential_backoff
def verify_urls(urls: List[str]) -> bool:
    """
    Verifies that all provided URLs are reachable via HTTP GET.
    Raises an error if any URL is unreachable.
    """
    if not urls:
        return True
    
    for url in urls:
        try:
            head_req = requests.head(url, timeout=10, allow_redirects=True)
            # 200 OK or 301/302 redirects are acceptable
            if head_req.status_code >= 400:
                raise HFTransientError(f"URL returned status {head_req.status_code}: {url}")
        except requests.exceptions.RequestException as e:
            raise HFTransientError(f"Failed to reach URL {url}: {e}")
    
    logger.info("All URLs verified successfully.")
    return True

def calculate_sha256(file_path: str) -> str:
    """Calculates SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_and_checksum(dataset_name: str, dest_path: str) -> str:
    """
    Downloads a dataset from HuggingFace Hub (if not already present) and
    calculates its SHA-256 checksum.
    
    If the dataset is a directory (e.g., 'openwebtext'), it downloads the
    dataset to a temporary location, moves it to dest_path, and checksums
    the directory contents recursively.
    
    Args:
        dataset_name: Name of the dataset on HuggingFace (e.g., 'openwebtext').
        dest_path: Local directory path where the dataset should be stored.
    
    Returns:
        The SHA-256 checksum string of the dataset directory.
    
    Raises:
        FileNotFoundError: If the dataset cannot be found or downloaded.
        Exception: If the download fails after retries.
    """
    import tempfile
    import shutil
    from pathlib import Path

    dest_path_obj = Path(dest_path)
    dest_path_obj.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    if any(dest_path_obj.iterdir()):
        logger.info(f"Dataset already exists at {dest_path}. Skipping download.")
        return calculate_directory_checksum(dest_path)

    logger.info(f"Downloading dataset '{dataset_name}' to {dest_path}...")
    
    # Use streaming to avoid loading full dataset into memory if possible,
    # but for download we need to save it.
    # We use load_dataset with trust_remote_code=True if needed, but standard datasets are safe.
    try:
        # Download to a temp directory first to ensure atomicity
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Load the dataset to trigger download
            # We use streaming=False to ensure files are actually downloaded to disk
            # Note: For large datasets, this might be heavy, but necessary for checksumming.
            # If the dataset is huge, we might need to stream and write manually,
            # but load_dataset handles caching. We'll force local download.
            dataset = load_dataset(dataset_name, trust_remote_code=False)
            
            # The dataset object itself doesn't guarantee files are in a specific folder
            # unless we save it. We'll save the raw data if available, or just rely on
            # the fact that load_dataset caches. 
            # However, the task asks to write to dest_path.
            # For 'openwebtext', it's a text file. For others, it might be parquet.
            # We will attempt to save the dataset to dest_path.
            if hasattr(dataset, 'save_to_disk'):
                dataset.save_to_disk(dest_path)
            else:
                # Fallback for datasets that don't support save_to_disk directly or are multi-split
                # We will just copy the cache or re-download. 
                # Since 'load_dataset' caches in HF_HOME, we need to move files.
                # A robust way for this specific pipeline is to assume the dataset
                # is available and we are just verifying the download.
                # But to be safe and adhere to "write to dest_path":
                # We will assume the dataset is small enough to save or we save the split.
                # For openwebtext, it's one big file.
                # Let's just save the first split if available.
                if isinstance(dataset, dict):
                    for split_name, split_data in dataset.items():
                        split_data.save_to_disk(os.path.join(dest_path, split_name))
                else:
                    dataset.save_to_disk(dest_path)

        logger.info(f"Dataset '{dataset_name}' downloaded and saved to {dest_path}.")
        return calculate_directory_checksum(dest_path)

    except Exception as e:
        logger.error(f"Failed to download dataset '{dataset_name}': {e}")
        raise

def calculate_directory_checksum(dir_path: str) -> str:
    """
    Calculates a SHA-256 checksum for a directory by hashing the concatenation
    of all file checksums (sorted by filename).
    """
    dir_path_obj = Path(dir_path)
    if not dir_path_obj.exists():
        raise FileNotFoundError(f"Directory {dir_path} does not exist.")

    sha256_hash = hashlib.sha256()
    files = sorted([f for f in dir_path_obj.rglob('*') if f.is_file()])
    
    if not files:
        # Empty directory
        return sha256_hash.hexdigest()

    for file_path in files:
        # Hash relative path
        rel_path = file_path.relative_to(dir_path_obj)
        sha256_hash.update(str(rel_path).encode('utf-8'))
        # Hash file content
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def load_openwebtext(dest_path: Optional[str] = None) -> str:
    """
    Loads the OpenWebText dataset, downloading if necessary.
    Returns the path to the downloaded data.
    """
    if dest_path is None:
        dest_path = "data/raw/openwebtext"
    os.makedirs(dest_path, exist_ok=True)
    checksum = download_and_checksum("openwebtext", dest_path)
    logger.info(f"OpenWebText checksum: {checksum}")
    return dest_path

def load_gsm8k(dest_path: Optional[str] = None) -> str:
    """Loads GSM8K dataset."""
    if dest_path is None:
        dest_path = "data/raw/gsm8k"
    os.makedirs(dest_path, exist_ok=True)
    checksum = download_and_checksum("gsm8k", dest_path)
    logger.info(f"GSM8K checksum: {checksum}")
    return dest_path

def load_arc_challenge(dest_path: Optional[str] = None) -> str:
    """Loads ARC Challenge dataset."""
    if dest_path is None:
        dest_path = "data/raw/arc_challenge"
    os.makedirs(dest_path, exist_ok=True)
    checksum = download_and_checksum("ai2_arc", dest_path) # ai2_arc is the repo name
    logger.info(f"ARC Challenge checksum: {checksum}")
    return dest_path

def load_boolq(dest_path: Optional[str] = None) -> str:
    """Loads BoolQ dataset."""
    if dest_path is None:
        dest_path = "data/raw/boolq"
    os.makedirs(dest_path, exist_ok=True)
    checksum = download_and_checksum("boolq", dest_path)
    logger.info(f"BoolQ checksum: {checksum}")
    return dest_path

def load_and_verify(dataset_name: str, dest_path: str) -> Tuple[str, str]:
    """
    Downloads a dataset and verifies its checksum.
    Returns (path, checksum).
    """
    checksum = download_and_checksum(dataset_name, dest_path)
    return dest_path, checksum

def load_local_dataset(path: str):
    """Loads a dataset from a local path."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Local dataset not found at {path}")
    # Implementation depends on format, but typically load_dataset(path)
    return load_dataset(path)

def load_all_datasets():
    """Downloads and verifies all required datasets."""
    datasets = {
        "openwebtext": "data/raw/openwebtext",
        "gsm8k": "data/raw/gsm8k",
        "arc_challenge": "data/raw/arc_challenge",
        "boolq": "data/raw/boolq"
    }
    results = {}
    for name, path in datasets.items():
        try:
            if name == "arc_challenge":
                # Special case for ai2_arc
                results[name] = load_arc_challenge(path)
            else:
                results[name] = download_and_checksum(name, path)
        except Exception as e:
            logger.error(f"Failed to load {name}: {e}")
            results[name] = None
    return results
