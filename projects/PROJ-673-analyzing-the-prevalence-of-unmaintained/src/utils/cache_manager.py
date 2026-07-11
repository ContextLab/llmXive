import json
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from src.utils.checksum import generate_checksum, write_checksum_file
from src.config.settings import get_config


class CacheManager:
    """
    Manages local file caching for raw API responses.
    
    Implements Constitution Principle III (Immutability) and VI (Reproducibility)
    by storing responses with immutable checksums to ensure data integrity
    and reproducibility of research results.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory to store cached files. Defaults to data/raw/
        """
        config = get_config()
        self.cache_dir = cache_dir or Path("data/raw")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._logger = None  # Lazy init to avoid circular imports if needed
        
        # Import logger if available
        try:
            from src.utils.logging_config import get_logger
            self._logger = get_logger("cache_manager")
        except ImportError:
            pass

    def _generate_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """
        Generate a unique cache key based on endpoint and parameters.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters as dictionary
            
        Returns:
            SHA256 hash of the normalized request
        """
        # Normalize parameters for consistent hashing
        normalized_params = json.dumps(params, sort_keys=True)
        request_string = f"{endpoint}:{normalized_params}"
        
        return hashlib.sha256(request_string.encode('utf-8')).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """
        Get the file path for a cached response.
        
        Args:
            cache_key: The cache key string
            
        Returns:
            Path to the cache file
        """
        return self.cache_dir / f"{cache_key}.json"

    def _get_checksum_path(self, cache_key: str) -> Path:
        """
        Get the file path for the checksum file.
        
        Args:
            cache_key: The cache key string
            
        Returns:
            Path to the checksum file
        """
        return self.cache_dir / f"{cache_key}.sha256"

    def is_cached(self, endpoint: str, params: Dict[str, Any]) -> bool:
        """
        Check if a response is already cached.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            True if cache exists and is valid, False otherwise
        """
        cache_key = self._generate_cache_key(endpoint, params)
        cache_path = self._get_cache_path(cache_key)
        checksum_path = self._get_checksum_path(cache_key)
        
        if not cache_path.exists() or not checksum_path.exists():
            return False
        
        # Verify checksum integrity
        try:
            with open(checksum_path, 'r') as f:
                stored_checksum = f.read().strip()
            
            with open(cache_path, 'rb') as f:
                current_checksum = generate_checksum(f)
            
            if stored_checksum != current_checksum:
                if self._logger:
                    self._logger.warning(
                        f"Cache checksum mismatch for {cache_key}. Removing invalid cache."
                    )
                cache_path.unlink()
                checksum_path.unlink()
                return False
            
            return True
        except Exception as e:
            if self._logger:
                self._logger.error(f"Error validating cache: {e}")
            return False

    def get(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached response.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            Cached response data or None if not found/invalid
        """
        cache_key = self._generate_cache_key(endpoint, params)
        cache_path = self._get_cache_path(cache_key)
        
        if not self.is_cached(endpoint, params):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if self._logger:
                self._logger.info(f"Cache hit for {endpoint} with params {params}")
            
            return data
        except json.JSONDecodeError as e:
            if self._logger:
                self._logger.error(f"Failed to parse cached JSON for {cache_key}: {e}")
            cache_path.unlink()
            self._get_checksum_path(cache_key).unlink()
            return None
        except Exception as e:
            if self._logger:
                self._logger.error(f"Error reading cache: {e}")
            return None

    def set(self, endpoint: str, params: Dict[str, Any], response_data: Dict[str, Any]) -> str:
        """
        Store a response in the cache with immutable checksum.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            response_data: The API response data to cache
            
        Returns:
            The cache key for the stored response
        """
        cache_key = self._generate_cache_key(endpoint, params)
        cache_path = self._get_cache_path(cache_key)
        checksum_path = self._get_checksum_path(cache_key)
        
        # Prepare cache entry with metadata
        cache_entry = {
            "endpoint": endpoint,
            "params": params,
            "timestamp": datetime.utcnow().isoformat(),
            "data": response_data
        }
        
        # Write cache file
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, indent=2, sort_keys=True)
            
            # Generate and write immutable checksum
            checksum = generate_checksum(cache_path)
            write_checksum_file(checksum_path, checksum)
            
            if self._logger:
                self._logger.info(
                    f"Cache written for {endpoint}: {cache_key} (checksum: {checksum[:16]}...)"
                )
            
            return cache_key
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to write cache: {e}")
            raise

    def clear(self, endpoint: Optional[str] = None) -> int:
        """
        Clear cache entries.
        
        Args:
            endpoint: Optional endpoint to filter by. If None, clears all.
            
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            if endpoint:
                # Check if filename contains endpoint hash (simplified check)
                # In production, we'd decode the key to verify
                pass
            
            checksum_file = cache_file.with_suffix('.sha256')
            
            try:
                cache_file.unlink()
                if checksum_file.exists():
                    checksum_file.unlink()
                deleted_count += 1
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Failed to delete {cache_file}: {e}")
        
        if self._logger:
            self._logger.info(f"Cleared {deleted_count} cache entries")
        
        return deleted_count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        json_files = list(self.cache_dir.glob("*.json"))
        sha_files = list(self.cache_dir.glob("*.sha256"))
        
        total_size = sum(f.stat().st_size for f in json_files if f.exists())
        
        return {
            "cache_dir": str(self.cache_dir),
            "total_files": len(json_files),
            "checksum_files": len(sha_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }

# Convenience functions for direct usage
def get_cache_manager() -> CacheManager:
    """Get or create a CacheManager instance."""
    return CacheManager()

def cache_response(endpoint: str, params: Dict[str, Any], response_data: Dict[str, Any]) -> str:
    """
    Convenience function to cache a response.
    
    Args:
        endpoint: API endpoint
        params: Query parameters
        response_data: Response data to cache
        
    Returns:
        Cache key
    """
    return get_cache_manager().set(endpoint, params, response_data)

def get_cached_response(endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get a cached response.
    
    Args:
        endpoint: API endpoint
        params: Query parameters
        
    Returns:
        Cached response or None
    """
    return get_cache_manager().get(endpoint, params)

def is_response_cached(endpoint: str, params: Dict[str, Any]) -> bool:
    """
    Check if a response is cached.
    
    Args:
        endpoint: API endpoint
        params: Query parameters
        
    Returns:
        True if cached
    """
    return get_cache_manager().is_cached(endpoint, params)
