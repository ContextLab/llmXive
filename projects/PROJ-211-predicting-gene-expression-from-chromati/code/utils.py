import os
import hashlib
import logging
import time
from typing import Optional, Callable, Any, Tuple
import requests
import json

logger = logging.getLogger(__name__)

def checksum_file(path: str) -> str:
    """Calculate the SHA256 checksum of a file.
    
    Args:
        path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise IOError(f"Error reading file {path}: {e}")

def load_config(config_path: str) -> dict:
    """Load a YAML or JSON configuration file.
    
    Args:
        config_path: Path to the config file.
        
    Returns:
        Dictionary containing the configuration.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            try:
                import yaml
                return yaml.safe_load(f)
            except ImportError:
                raise ImportError("PyYAML is required to load YAML config files. Install it with 'pip install pyyaml'.")
        elif config_path.endswith('.json'):
            return json.load(f)
        else:
            raise ValueError(f"Unsupported config format: {config_path}")

def retry_request(func: Callable, url: str, max_retries: int = 3, delay: float = 2.0) -> Tuple[bool, Any]:
    """Execute a request with retry logic.
    
    Args:
        func: The request function (e.g., requests.get).
        url: The URL to request.
        max_retries: Maximum number of retry attempts.
        delay: Delay in seconds between retries.
        
    Returns:
        Tuple of (success: bool, result: Any).
    """
    for attempt in range(max_retries):
        try:
            response = func(url)
            response.raise_for_status()
            return True, response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                logger.error(f"Request failed after {max_retries} attempts: {e}")
                return False, None
    return False, None