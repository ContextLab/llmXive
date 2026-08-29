"""
Disk-based caching mechanism for function samples.
"""
import json
import os
import hashlib
import time
from pathlib import Path
from typing import Optional, Any, Dict
from utils.logging import CacheError, get_logger

logger = get_logger(__name__)

class Cache:
    """Disk-based cache keyed by function hash."""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cache initialized at {self.cache_dir}")

    def compute_hash(self, data: str) -> str:
        """Compute SHA256 hash of input data."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve item from cache."""
        path = self.cache_dir / f"{key}.json"
        if not path.exists():
            return None
        
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read cache for {key}: {e}")
            return None

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Store item in cache."""
        path = self.cache_dir / f"{key}.json"
        try:
            with open(path, 'w') as f:
                json.dump(value, f, indent=2)
        except IOError as e:
            raise CacheError(f"Failed to write cache for {key}: {e}")

    def clear(self) -> None:
        """Clear all cache entries."""
        for f in self.cache_dir.glob("*.json"):
            f.unlink()
        logger.info("Cache cleared")

# Global cache instance
_cache: Optional[Cache] = None

def get_cache(cache_dir: str = "data/cache") -> Cache:
    global _cache
    if _cache is None:
        _cache = Cache(cache_dir)
    return _cache

def cache_get(key: str) -> Optional[Dict[str, Any]]:
    return get_cache().get(key)

def cache_set(key: str, value: Dict[str, Any]) -> None:
    get_cache().set(key, value)

def compute_hash(data: str) -> str:
    return get_cache().compute_hash(data)
