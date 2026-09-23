"""
Local file caching mechanism for raw API responses.
Implements Constitution Principle III & VI: Immutable checksums and reproducibility.
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Ensure the cache directory exists
CACHE_DIR = Path("data/raw")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _generate_cache_key(request_params: dict) -> str:
    """
    Generate a deterministic hash key from request parameters.
    This ensures the same request always maps to the same cache file.
    """
    # Sort keys to ensure deterministic serialization
    serialized = json.dumps(request_params, sort_keys=True)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

def _generate_timestamp_suffix() -> str:
    """
    Generate a timestamp suffix for the filename to ensure uniqueness
    even if the same request is made multiple times (immutability).
    """
    from datetime import datetime
    return datetime.now().isoformat().replace(":", "-").replace(".", "-")

def save_response_to_cache(request_params: dict, response: dict) -> str:
    """
    Save an API response to the local cache.

    Args:
        request_params (dict): The parameters used for the API request.
        response (dict): The raw response data from the API.

    Returns:
        str: The checksum of the saved file.

    Raises:
        ValueError: If response is not serializable.
        IOError: If writing to disk fails.
    """
    try:
        # Serialize the response to ensure it's valid JSON
        response_json = json.dumps(response, indent=2, default=str)
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize response: {e}")
        raise ValueError(f"Response is not JSON serializable: {e}")

    # Generate the cache key
    cache_key = _generate_cache_key(request_params)
    timestamp = _generate_timestamp_suffix()

    # Construct the filename: {key}_{timestamp}.json
    filename = f"{cache_key}_{timestamp}.json"
    file_path = CACHE_DIR / filename

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(response_json)
        
        # Compute and store checksum for integrity verification
        checksum = hashlib.md5(response_json.encode('utf-8')).hexdigest()
        
        # Optional: Store checksum in a sidecar file for explicit verification
        checksum_path = file_path.with_suffix('.json.md5')
        with open(checksum_path, 'w', encoding='utf-8') as f:
            f.write(checksum)
        
        logger.info(f"Response cached to {file_path} with checksum {checksum}")
        return checksum

    except IOError as e:
        logger.error(f"Failed to write cache file {file_path}: {e}")
        raise IOError(f"Failed to write cache file: {e}")

def load_from_cache(request_params: dict) -> Optional[dict]:
    """
    Load a response from the cache if it exists.
    
    Note: This function looks for ANY file matching the request hash prefix.
    Since we append timestamps to ensure immutability, we search for files
    starting with the generated key.

    Args:
        request_params (dict): The parameters used for the API request.

    Returns:
        dict | None: The cached response data, or None if not found.
    """
    cache_key = _generate_cache_key(request_params)
    
    # Search for files matching the key pattern
    # Since we use {key}_{timestamp}.json, we search for files starting with key_
    matching_files = list(CACHE_DIR.glob(f"{cache_key}_*.json"))
    
    if not matching_files:
        logger.debug(f"No cache hit for request key: {cache_key}")
        return None

    # For reproducibility, we usually want the *first* cached version or the *latest*.
    # Given the requirement for "immutable checksums", we should treat the cache
    # as read-only once written. We will return the first match found.
    # In a real scenario, we might want to verify checksums.
    cache_file = matching_files[0]
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Verify integrity if checksum file exists
        checksum_file = cache_file.with_suffix('.json.md5')
        if checksum_file.exists():
            with open(checksum_file, 'r', encoding='utf-8') as f:
                stored_checksum = f.read().strip()
            
            current_content = json.dumps(data, sort_keys=True) # Re-serialize to compare
            current_checksum = hashlib.md5(current_content.encode('utf-8')).hexdigest()
            
            if stored_checksum != current_checksum:
                logger.warning(f"Checksum mismatch for {cache_file}. Data may be corrupted.")
                return None
        
        logger.info(f"Cache hit for request key: {cache_key} from {cache_file}")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in cache file {cache_file}: {e}")
        return None
    except IOError as e:
        logger.error(f"Failed to read cache file {cache_file}: {e}")
        return None