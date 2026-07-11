import os
import hashlib
import logging
import time
from typing import Optional, Callable, Any, Tuple
import requests
import yaml

def checksum_file(path: str) -> str:
    """
    Calculate SHA256 checksum of a file.
    
    Args:
        path: Path to the file to checksum.
        
    Returns:
        Hexadecimal SHA256 checksum string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def load_config(config_path: str) -> dict:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the YAML configuration file.
        
    Returns:
        Dictionary containing configuration values.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the YAML is invalid.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config or {}

def retry_request(
    func: Callable,
    max_attempts: int = 3,
    delay_seconds: int = 5,
    *args,
    **kwargs
) -> Tuple[bool, Any]:
    """
    Retry a function call with fixed time intervals.
    
    This function implements error handling and retry logic for data fetching.
    It attempts to execute the provided function up to `max_attempts` times.
    If an exception occurs, it waits for a fixed `delay_seconds` interval before
    retrying, rather than using exponential backoff.
    
    Args:
        func: The function to call (must accept *args, **kwargs).
        max_attempts: Maximum number of retry attempts.
        delay_seconds: Fixed delay between retries in seconds.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
        
    Returns:
        Tuple of (success: bool, result: Any).
    """
    attempt = 0
    
    while attempt < max_attempts:
        try:
            result = func(*args, **kwargs)
            return True, result
        except requests.RequestException as e:
            attempt += 1
            if attempt >= max_attempts:
                logging.error(f"Request failed after {max_attempts} attempts: {e}")
                return False, None
            
            logging.warning(
                f"Request failed (attempt {attempt}/{max_attempts}): {e}. "
                f"Retrying in {delay_seconds}s..."
            )
            time.sleep(delay_seconds)
    
    return False, None