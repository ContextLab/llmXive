"""
Disk-based caching mechanism for function samples and analysis results.
Keyed by function hash to prevent redundant computation.
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
    """Disk-based cache keyed by function hash with TTL support."""
    
    def __init__(self, cache_dir: str = "data/cache", ttl_seconds: int = 86400):
        """
        Initialize the cache.
        
        Args:
            cache_dir: Directory path for cache storage.
            ttl_seconds: Time-to-live for cache entries in seconds (default: 24 hours).
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        logger.info(f"Cache initialized at {self.cache_dir} with TTL={ttl_seconds}s")

    def compute_hash(self, data: str) -> str:
        """Compute SHA256 hash of input data."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """Construct the full path for a cache key."""
        return self.cache_dir / f"{key}.json"

    def _is_expired(self, metadata: Dict[str, Any]) -> bool:
        """Check if a cache entry has expired based on TTL."""
        created_at = metadata.get('created_at', 0)
        current_time = time.time()
        return (current_time - created_at) > self.ttl_seconds

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve item from cache if it exists and hasn't expired.
        
        Args:
            key: The cache key (typically a function hash).
        
        Returns:
            The cached data dictionary if found and valid, None otherwise.
        """
        path = self._get_cache_path(key)
        if not path.exists():
            logger.debug(f"Cache miss for key {key}: file not found")
            return None
        
        try:
            with open(path, 'r') as f:
                entry = json.load(f)
            
            # Check for metadata and TTL
            if isinstance(entry, dict) and 'data' in entry and 'metadata' in entry:
                if self._is_expired(entry['metadata']):
                    logger.info(f"Cache entry expired for key {key}, removing")
                    path.unlink()
                    return None
                return entry['data']
            else:
                # Legacy format without metadata, treat as valid but warn
                logger.warning(f"Legacy cache format detected for key {key}, no TTL check applied")
                return entry
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read cache for {key}: {e}")
            # Corrupted entry, remove it
            try:
                path.unlink()
            except OSError:
                pass
            return None

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        Store item in cache with metadata.
        
        Args:
            key: The cache key.
            value: The data dictionary to cache.
        """
        path = self._get_cache_path(key)
        entry = {
            'data': value,
            'metadata': {
                'created_at': time.time(),
                'ttl_seconds': self.ttl_seconds
            }
        }
        try:
            with open(path, 'w') as f:
                json.dump(entry, f, indent=2)
            logger.debug(f"Cache set for key {key}")
        except IOError as e:
            raise CacheError(f"Failed to write cache for {key}: {e}")

    def clear(self) -> None:
        """Clear all cache entries."""
        count = 0
        for f in self.cache_dir.glob("*.json"):
            try:
                f.unlink()
                count += 1
            except OSError as e:
                logger.warning(f"Failed to delete cache file {f}: {e}")
        logger.info(f"Cache cleared: {count} entries removed")

    def delete(self, key: str) -> bool:
        """
        Delete a specific cache entry.
        
        Args:
            key: The cache key to delete.
        
        Returns:
            True if the entry was deleted, False if it didn't exist.
        """
        path = self._get_cache_path(key)
        if path.exists():
            try:
                path.unlink()
                logger.debug(f"Cache deleted for key {key}")
                return True
            except OSError as e:
                logger.warning(f"Failed to delete cache file {path}: {e}")
                return False
        return False

    def stats(self) -> Dict[str, Any]:
        """Return statistics about the cache."""
        files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)
        return {
            'entry_count': len(files),
            'total_size_bytes': total_size,
            'cache_dir': str(self.cache_dir),
            'ttl_seconds': self.ttl_seconds
        }

# Global cache instance
_cache: Optional[Cache] = None

def get_cache(cache_dir: str = "data/cache", ttl_seconds: int = 86400) -> Cache:
    """
    Get or create the global cache instance.
    
    Args:
        cache_dir: Directory path for cache storage.
        ttl_seconds: Time-to-live for cache entries.
    
    Returns:
        The Cache instance.
    """
    global _cache
    if _cache is None:
        _cache = Cache(cache_dir, ttl_seconds)
    return _cache

def cache_get(key: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get from global cache."""
    return get_cache().get(key)

def cache_set(key: str, value: Dict[str, Any]) -> None:
    """Convenience function to set in global cache."""
    get_cache().set(key, value)

def cache_delete(key: str) -> bool:
    """Convenience function to delete from global cache."""
    return get_cache().delete(key)

def compute_hash(data: str) -> str:
    """Convenience function to compute hash using global cache instance."""
    return get_cache().compute_hash(data)
