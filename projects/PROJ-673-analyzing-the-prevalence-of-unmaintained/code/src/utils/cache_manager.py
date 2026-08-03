"""
Local file caching mechanism for raw API responses.

Implements Constitution Principle III (Immutable Data) and VI (Reproducibility)
by saving raw responses to data/raw/ with immutable SHA-256 checksums.
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime
import time

from src.utils.checksum import generate_checksum, write_checksum_file

# Configure logging
logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages local caching of raw API responses with immutable checksums.
    
    Caches are stored in data/raw/ directory with the following structure:
    data/raw/
        <cache_key>.json        # The cached response data
        <cache_key>.sha256      # The checksum file for verification
    """
    
    def __init__(self, cache_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory path for storing cached files. Defaults to 'data/raw'.
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path("data/raw")
        self._ensure_cache_dir()
        logger.info(f"Cache manager initialized with directory: {self.cache_dir}")
    
    def _ensure_cache_dir(self) -> None:
        """Create the cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_cache_key(self, api_name: str, endpoint: str, params: Dict[str, Any]) -> str:
        """
        Generate a deterministic cache key from API parameters.
        
        Args:
            api_name: Name of the API (e.g., 'npm', 'github')
            endpoint: API endpoint path
            params: Dictionary of query parameters
        
        Returns:
            A deterministic string key for the cache.
        """
        # Sort params to ensure deterministic ordering
        sorted_params = sorted(params.items()) if params else []
        key_data = f"{api_name}:{endpoint}:{sorted_params}"
        # Use a shorter hash for file names
        return hashlib.md5(key_data.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the path for a cached file given its key."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _get_checksum_path(self, cache_key: str) -> Path:
        """Get the path for a checksum file given its key."""
        return self.cache_dir / f"{cache_key}.sha256"
    
    def _is_cache_valid(self, cache_key: str, response_data: Dict[str, Any]) -> bool:
        """
        Check if an existing cache is valid by verifying the checksum.
        
        Args:
            cache_key: The cache key to check
            response_data: The current response data to verify against
        
        Returns:
            True if cache exists and is valid, False otherwise.
        """
        cache_path = self._get_cache_path(cache_key)
        checksum_path = self._get_checksum_path(cache_key)
        
        if not cache_path.exists() or not checksum_path.exists():
            return False
        
        try:
            # Read existing checksum
            with open(checksum_path, 'r') as f:
                stored_checksum = f.read().strip()
            
            # Generate checksum for current data
            current_checksum = generate_checksum(response_data)
            
            if stored_checksum != current_checksum:
                logger.warning(f"Checksum mismatch for cache key {cache_key}. Cache invalid.")
                return False
            
            # Check file age (optional: could add TTL logic here)
            file_age = time.time() - cache_path.stat().st_mtime
            logger.debug(f"Cache hit for {cache_key}. File age: {file_age:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Error validating cache for {cache_key}: {e}")
            return False
    
    def cache_response(self, api_name: str, endpoint: str, params: Dict[str, Any], 
                     response_data: Dict[str, Any]) -> None:
        """
        Save an API response to the local cache with a checksum.
        
        Args:
            api_name: Name of the API (e.g., 'npm', 'github')
            endpoint: API endpoint path
            params: Query parameters used for the request
            response_data: The raw response data to cache
        """
        cache_key = self._generate_cache_key(api_name, endpoint, params)
        cache_path = self._get_cache_path(cache_key)
        checksum_path = self._get_checksum_path(cache_key)
        
        try:
            # Write the response data
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, sort_keys=True)
            
            # Generate and write the checksum
            checksum = generate_checksum(response_data)
            write_checksum_file(checksum_path, checksum)
            
            logger.info(f"Cached response for {api_name}:{endpoint} (key: {cache_key})")
            
        except Exception as e:
            logger.error(f"Failed to cache response for {api_name}:{endpoint}: {e}")
            raise
    
    def get_cached_response(self, api_name: str, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached response if it exists and is valid.
        
        Args:
            api_name: Name of the API
            endpoint: API endpoint path
            params: Query parameters used for the request
        
        Returns:
            The cached response data if valid, None otherwise.
        """
        cache_key = self._generate_cache_key(api_name, endpoint, params)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                response_data = json.load(f)
            
            # Verify checksum before returning
            if self._is_cache_valid(cache_key, response_data):
                return response_data
            else:
                logger.warning(f"Cache invalid for {api_name}:{endpoint}, fetching fresh data.")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Corrupt cache file for {api_name}:{endpoint}: {e}")
            # Clean up corrupt file
            cache_path.unlink(missing_ok=True)
            self._get_checksum_path(cache_key).unlink(missing_ok=True)
            return None
        except Exception as e:
            logger.error(f"Error reading cache for {api_name}:{endpoint}: {e}")
            return None
    
    def clear_cache(self, cache_key: Optional[str] = None) -> int:
        """
        Clear cached files.
        
        Args:
            cache_key: If provided, clear only this specific cache entry.
                      If None, clear all cache entries.
        
        Returns:
            Number of files deleted.
        """
        deleted_count = 0
        
        if cache_key:
            files_to_delete = [
                self._get_cache_path(cache_key),
                self._get_checksum_path(cache_key)
            ]
        else:
            files_to_delete = list(self.cache_dir.glob("*.json")) + \
                            list(self.cache_dir.glob("*.sha256"))
        
        for file_path in files_to_delete:
            try:
                if file_path.exists():
                    file_path.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted cache file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {e}")
        
        return deleted_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current cache.
        
        Returns:
            Dictionary with cache statistics.
        """
        json_files = list(self.cache_dir.glob("*.json"))
        sha_files = list(self.cache_dir.glob("*.sha256"))
        
        total_size = sum(f.stat().st_size for f in json_files if f.exists())
        
        return {
            "cache_dir": str(self.cache_dir),
            "total_entries": len(json_files),
            "checksum_files": len(sha_files),
            "total_size_bytes": total_size,
            "last_modified": max((f.stat().st_mtime for f in json_files), default=None)
        }


# Convenience functions for quick usage
_default_cache: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create the default cache manager instance."""
    global _default_cache
    if _default_cache is None:
        _default_cache = CacheManager()
    return _default_cache


def cache_api_response(api_name: str, endpoint: str, params: Dict[str, Any], 
                     response_data: Dict[str, Any]) -> None:
    """Convenience function to cache an API response."""
    get_cache_manager().cache_response(api_name, endpoint, params, response_data)


def get_cached_api_response(api_name: str, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convenience function to retrieve a cached API response."""
    return get_cache_manager().get_cached_response(api_name, endpoint, params)
    
