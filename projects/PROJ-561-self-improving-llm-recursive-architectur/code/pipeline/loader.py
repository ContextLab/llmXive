import time
import os
import logging
import hashlib
import requests
from functools import wraps
from typing import List, Optional, Iterator, Dict, Any
from datasets import load_dataset

from pipeline.config import get_config
from pipeline.loader import exponential_backoff

logger = logging.getLogger(__name__)

class HFTransientError(Exception):
    """Exception raised for transient Hugging Face dataset errors."""
    pass

def exponential_backoff(func):
    """
    Decorator that adds exponential backoff retry logic to a function.
    Initial delay: 2 seconds, Max retries: 5, Max delay: 60 seconds.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        retries = 0
        max_retries = 5
        initial_delay = 2
        max_delay = 60
        
        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except (requests.exceptions.RequestException, ConnectionError, 
                    TimeoutError, HFTransientError) as e:
                retries += 1
                if retries >= max_retries:
                    logger.error(f"Failed after {max_retries} retries: {e}")
                    raise
                delay = min(initial_delay * (2 ** (retries - 1)), max_delay)
                logger.warning(f"Retry {retries}/{max_retries} in {delay}s due to {e}")
                time.sleep(delay)
        return func(*args, **kwargs)
    return wrapper

@exponential_backoff
def verify_urls(urls: List[str]) -> bool:
    """
    Verifies that a list of URLs are reachable.
    Raises an error if any URL is unreachable.
    """
    for url in urls:
        try:
            response = requests.head(url, timeout=10)
            if response.status_code >= 400:
                raise HFTransientError(f"URL {url} returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            raise HFTransientError(f"URL {url} is unreachable: {e}")
    return True

@exponential_backoff
def download_and_checksum(dataset_name: str, dest_path: str) -> str:
    """
    Downloads a dataset and writes its SHA-256 checksum.
    Note: For HF datasets, this function verifies availability and calculates
    a checksum of the cached metadata or a representative file if direct download
    isn't the standard path. For this implementation, we verify the dataset
    exists and write a checksum of the dataset info.
    """
    try:
        # Attempt to load dataset info to verify existence
        ds = load_dataset(dataset_name, split="train", streaming=True)
        first_item = next(iter(ds))
        
        # Create checksum of the first item's string representation as a proxy
        # In a real pipeline, this might checksum a specific shard file
        content = str(first_item).encode('utf-8')
        checksum = hashlib.sha256(content).hexdigest()
        
        checksum_path = dest_path + ".sha256"
        with open(checksum_path, 'w') as f:
            f.write(checksum)
        
        logger.info(f"Verified {dataset_name}, checksum: {checksum}")
        return checksum
    except Exception as e:
        raise HFTransientError(f"Failed to verify/download {dataset_name}: {e}")

def calculate_directory_checksum(dir_path: str) -> Optional[str]:
    """Calculates SHA-256 checksum of all files in a directory."""
    if not os.path.exists(dir_path):
        return None
    
    hasher = hashlib.sha256()
    for root, _, files in os.walk(dir_path):
        for file in sorted(files):
            if file.endswith('.sha256'):
                continue
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
    return hasher.hexdigest()

@exponential_backoff
def load_openwebtext(split: str = "train", streaming: bool = True) -> Iterator[Dict[str, Any]]:
    """
    Loads OpenWebText dataset with streaming support.
    Uses fail-fast logic: if the dataset is unavailable, it raises immediately.
    """
    try:
        # OpenWebText is not publicly available on HF Hub directly anymore without auth
        # or a specific mirror. We use 'stas/openwebtext' which is a common mirror.
        dataset = load_dataset("stas/openwebtext", split=split, streaming=streaming)
        logger.info("Successfully loaded OpenWebText dataset")
        return iter(dataset)
    except Exception as e:
        logger.error(f"Failed to load OpenWebText: {e}")
        raise FileNotFoundError(f"OpenWebText dataset not found or inaccessible: {e}")

@exponential_backoff
def load_gsm8k(split: str = "train", streaming: bool = True) -> Iterator[Dict[str, Any]]:
    """
    Loads GSM8K dataset with streaming support.
    """
    try:
        dataset = load_dataset("gsm8k", "main", split=split, streaming=streaming)
        logger.info("Successfully loaded GSM8K dataset")
        return iter(dataset)
    except Exception as e:
        logger.error(f"Failed to load GSM8K: {e}")
        raise FileNotFoundError(f"GSM8K dataset not found or inaccessible: {e}")

@exponential_backoff
def load_arc_challenge(split: str = "train", streaming: bool = True) -> Iterator[Dict[str, Any]]:
    """
    Loads ARC-Challenge dataset with streaming support.
    """
    try:
        dataset = load_dataset("ai2_arc", "ARC-Challenge", split=split, streaming=streaming)
        logger.info("Successfully loaded ARC-Challenge dataset")
        return iter(dataset)
    except Exception as e:
        logger.error(f"Failed to load ARC-Challenge: {e}")
        raise FileNotFoundError(f"ARC-Challenge dataset not found or inaccessible: {e}")

@exponential_backoff
def load_boolq(split: str = "train", streaming: bool = True) -> Iterator[Dict[str, Any]]:
    """
    Loads BoolQ dataset with streaming support.
    """
    try:
        dataset = load_dataset("boolq", split=split, streaming=streaming)
        logger.info("Successfully loaded BoolQ dataset")
        return iter(dataset)
    except Exception as e:
        logger.error(f"Failed to load BoolQ: {e}")
        raise FileNotFoundError(f"BoolQ dataset not found or inaccessible: {e}")

def load_and_verify(dataset_name: str, split: str = "train", streaming: bool = True):
    """
    Generic loader that verifies and loads a dataset by name.
    """
    loaders = {
        "openwebtext": load_openwebtext,
        "gsm8k": load_gsm8k,
        "arc_challenge": load_arc_challenge,
        "boolq": load_boolq
    }
    
    if dataset_name not in loaders:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    return loaders[dataset_name](split=split, streaming=streaming)

def load_local_dataset(path: str, split: str = "train") -> Iterator[Dict[str, Any]]:
    """
    Loads a local dataset from a JSON/JSONL file.
    """
    from datasets import load_dataset
    try:
        dataset = load_dataset("json", data_files=path, split=split)
        return iter(dataset)
    except Exception as e:
        raise FileNotFoundError(f"Local dataset not found at {path}: {e}")

def load_all_datasets(streaming: bool = True):
    """
    Loads all required datasets for the pipeline.
    Returns a dictionary of iterators.
    """
    return {
        "openwebtext": load_openwebtext(streaming=streaming),
        "gsm8k": load_gsm8k(streaming=streaming),
        "arc_challenge": load_arc_challenge(streaming=streaming),
        "boolq": load_boolq(streaming=streaming)
    }