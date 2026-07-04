import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ..config.settings import get_data_dir


def compute_checksum(data: Any) -> str:
    """
    Compute a SHA-256 checksum of the given data.
    
    Args:
        data: The data to hash (will be JSON serialized if dict/list).
    
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    if isinstance(data, (dict, list)):
        # Sort keys for deterministic serialization
        serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    elif isinstance(data, str):
        serialized = data
    else:
        serialized = str(data)
    
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def get_cache_path(cache_key: str, checksum: str) -> Path:
    """
    Generate the file path for a cached response.
    
    The filename format is: {cache_key}_{checksum}.json
    This ensures immutability: if the data changes, the checksum changes,
    resulting in a new file name.
    
    Args:
        cache_key: A human-readable identifier for the data source/query.
        checksum: The SHA-256 checksum of the data content.
    
    Returns:
        Path object pointing to the cache file in data/raw/.
    """
    raw_dir = get_data_dir() / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{cache_key}_{checksum}.json"
    return raw_dir / filename


def save_to_cache(cache_key: str, data: Any) -> Path:
    """
    Save data to the local cache with an immutable checksum-based filename.
    
    Args:
        cache_key: Identifier for the data (e.g., 'npm_package_123').
        data: The data to cache (dict, list, or string).
    
    Returns:
        Path to the saved file.
    """
    checksum = compute_checksum(data)
    cache_path = get_cache_path(cache_key, checksum)
    
    # Only write if file doesn't exist (immutability principle)
    if not cache_path.exists():
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    return cache_path


def load_from_cache(cache_key: str, expected_checksum: str) -> Optional[Any]:
    """
    Load data from the cache if the checksum matches.
    
    Args:
        cache_key: Identifier for the data.
        expected_checksum: The expected SHA-256 checksum.
    
    Returns:
        The loaded data if the file exists and checksum matches, else None.
    """
    cache_path = get_cache_path(cache_key, expected_checksum)
    
    if not cache_path.exists():
        return None
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Verify integrity
        actual_checksum = compute_checksum(data)
        if actual_checksum == expected_checksum:
            return data
        else:
            # Data corruption or version mismatch
            return None
    except (json.JSONDecodeError, IOError):
        return None


def is_cached(cache_key: str, expected_checksum: str) -> bool:
    """
    Check if valid data exists in the cache.
    
    Args:
        cache_key: Identifier for the data.
        expected_checksum: The expected SHA-256 checksum.
    
    Returns:
        True if the file exists and checksum matches, False otherwise.
    """
    return load_from_cache(cache_key, expected_checksum) is not None
