"""
Disk-based caching mechanism for refactoring results.
Keyed by function hash to avoid redundant LLM API calls.
"""
import json
import os
import hashlib
import time
from pathlib import Path
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from .logging import CacheError, get_logger

logger = get_logger(__name__)

class Cache:
    """
    A disk-based cache for storing and retrieving refactoring results.
    Uses a simple JSON file structure where each entry is keyed by function hash.
    """

    def __init__(self, cache_dir: str = "data/cache", ttl_days: int = 30):
        """
        Initialize the cache.

        Args:
            cache_dir: Directory to store cache files. Defaults to 'data/cache'.
            ttl_days: Time-to-live for cache entries in days. Defaults to 30.
        """
        self.cache_dir = Path(cache_dir)
        self.ttl = timedelta(days=ttl_days)
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Create the cache directory if it doesn't exist."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Cache directory ensured at {self.cache_dir}")
        except OSError as e:
            logger.error(f"Failed to create cache directory {self.cache_dir}: {e}")
            raise CacheError(f"Failed to create cache directory: {e}")

    def _get_cache_path(self, key: str) -> Path:
        """
        Get the file path for a cache key.

        Args:
            key: The cache key (function hash).

        Returns:
            Path to the cache file.
        """
        # Sanitize key to ensure it's a valid filename
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_key}.json"

    def _compute_hash(self, data: str) -> str:
        """
        Compute a SHA-256 hash of the input data.

        Args:
            data: The string data to hash.

        Returns:
            Hexadecimal hash string.
        """
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a value from the cache.

        Args:
            key: The cache key (function hash).

        Returns:
            The cached data if found and not expired, None otherwise.
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            logger.debug(f"Cache miss for key {key[:8]}...: file not found")
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                entry = json.load(f)

            # Check TTL
            cached_time = datetime.fromisoformat(entry['timestamp'])
            if datetime.now() - cached_time > self.ttl:
                logger.info(f"Cache entry expired for key {key[:8]}...")
                cache_path.unlink()
                return None

            logger.debug(f"Cache hit for key {key[:8]}...")
            return entry['data']

        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"Failed to read cache entry for key {key[:8]}...: {e}")
            # Corrupt entry, remove it
            try:
                cache_path.unlink()
            except OSError:
                pass
            return None

    def set(self, key: str, data: Dict[str, Any]) -> None:
        """
        Store a value in the cache.

        Args:
            key: The cache key (function hash).
            data: The data to cache.
        """
        cache_path = self._get_cache_path(key)

        entry = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
            logger.debug(f"Cache set for key {key[:8]}...")
        except OSError as e:
            logger.error(f"Failed to write cache entry for key {key[:8]}...: {e}")
            raise CacheError(f"Failed to write cache entry: {e}")

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared.
        """
        count = 0
        try:
            for file_path in self.cache_dir.glob("*.json"):
                file_path.unlink()
                count += 1
            logger.info(f"Cleared {count} cache entries")
        except OSError as e:
            logger.error(f"Failed to clear cache: {e}")
            raise CacheError(f"Failed to clear cache: {e}")

        return count

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)

        expired_count = 0
        valid_count = 0

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    entry = json.load(f)
                    cached_time = datetime.fromisoformat(entry['timestamp'])
                    if datetime.now() - cached_time > self.ttl:
                        expired_count += 1
                    else:
                        valid_count += 1
            except (json.JSONDecodeError, KeyError, OSError):
                expired_count += 1

        return {
            'total_files': len(files),
            'valid_entries': valid_count,
            'expired_entries': expired_count,
            'total_size_bytes': total_size,
            'cache_dir': str(self.cache_dir),
            'ttl_days': self.ttl.days
        }


# Convenience functions for direct usage
_default_cache: Optional[Cache] = None

def get_cache() -> Cache:
    """Get or create the default cache instance."""
    global _default_cache
    if _default_cache is None:
        _default_cache = Cache()
    return _default_cache

def cache_get(key: str) -> Optional[Dict[str, Any]]:
    """Retrieve a value from the default cache."""
    return get_cache().get(key)

def cache_set(key: str, data: Dict[str, Any]) -> None:
    """Store a value in the default cache."""
    get_cache().set(key, data)

def compute_hash(data: str) -> str:
    """Compute a hash for the given data."""
    return Cache()._compute_hash(data)
