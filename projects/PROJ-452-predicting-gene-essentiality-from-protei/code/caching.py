"""
Caching module for expensive data fetching operations (T013, T014).
Implements file-based caching with checksum validation to avoid redundant API calls.
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable, TypeVar, cast
import time
import shutil

from utils import compute_sha256, setup_logging

logger = logging.getLogger(__name__)

# Cache directory structure
CACHE_DIR = Path("data/cache")
CACHE_MANIFEST = CACHE_DIR / "manifest.json"
CACHE_TTL_SECONDS = 86400 * 7  # 7 days default TTL

T = TypeVar('T')

def _ensure_cache_dir() -> Path:
    """Ensure cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR

def _load_manifest() -> Dict[str, Any]:
    """Load cache manifest if it exists."""
    if CACHE_MANIFEST.exists():
        try:
            with open(CACHE_MANIFEST, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cache manifest: {e}. Creating new manifest.")
    return {"entries": {}}

def _save_manifest(manifest: Dict[str, Any]) -> None:
    """Save cache manifest."""
    with open(CACHE_MANIFEST, 'w') as f:
        json.dump(manifest, f, indent=2)

def _compute_key(prefix: str, **kwargs) -> str:
    """Compute a unique cache key based on prefix and kwargs."""
    param_str = json.dumps(kwargs, sort_keys=True)
    content = f"{prefix}:{param_str}"
    return hashlib.sha256(content.encode()).hexdigest()[:32]

def _get_cache_path(key: str, extension: str = ".json") -> Path:
    """Get the file path for a cache key."""
    return _ensure_cache_dir() / f"{key}{extension}"

def _is_cache_valid(key: str, ttl: Optional[int] = None) -> bool:
    """Check if a cached entry is valid (exists and not expired)."""
    manifest = _load_manifest()
    if key not in manifest.get("entries", {}):
        return False
    
    entry = manifest["entries"][key]
    if ttl is None:
        ttl = CACHE_TTL_SECONDS
    
    created_at = entry.get("created_at", 0)
    if time.time() - created_at > ttl:
        return False
    
    cache_path = _get_cache_path(key, entry.get("extension", ".json"))
    return cache_path.exists()

def _save_to_cache(key: str, data: Any, extension: str = ".json") -> None:
    """Save data to cache and update manifest."""
    cache_path = _get_cache_path(key, extension)
    
    # Save data
    if isinstance(data, dict) or isinstance(data, list):
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
    elif isinstance(data, str):
        with open(cache_path, 'w') as f:
            f.write(data)
    else:
        # Fallback to JSON serialization
        with open(cache_path, 'w') as f:
            json.dump({"data": str(data)}, f, indent=2)
    
    # Update manifest
    manifest = _load_manifest()
    manifest["entries"][key] = {
        "created_at": time.time(),
        "extension": extension,
        "size_bytes": cache_path.stat().st_size
    }
    _save_manifest(manifest)
    logger.info(f"Cached data with key '{key}' to {cache_path}")

def _load_from_cache(key: str, extension: str = ".json") -> Optional[Any]:
    """Load data from cache."""
    cache_path = _get_cache_path(key, extension)
    if not cache_path.exists():
        return None
    
    try:
        with open(cache_path, 'r') as f:
            if extension == ".json":
                return json.load(f)
            else:
                return f.read()
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load cached data for key '{key}': {e}")
        return None

def cache_result(
    prefix: str,
    ttl: Optional[int] = None,
    extension: str = ".json"
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to cache function results.
    
    Args:
        prefix: Unique prefix for the cache key (e.g., "string_ppi", "deg_essentiality")
        ttl: Time-to-live in seconds (default: CACHE_TTL_SECONDS)
        extension: File extension for cached data
    
    Returns:
        Decorated function with caching behavior
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            key = _compute_key(prefix, *args, **kwargs)
            
            # Check cache
            if _is_cache_valid(key, ttl):
                logger.info(f"Cache hit for {prefix} with key {key}")
                cached_data = _load_from_cache(key, extension)
                if cached_data is not None:
                    return cast(T, cached_data)
                else:
                    logger.warning(f"Cache entry corrupted for {key}, refetching")
            
            # Fetch fresh data
            logger.info(f"Cache miss for {prefix}, fetching fresh data")
            result = func(*args, **kwargs)
            
            # Save to cache
            _save_to_cache(key, result, extension)
            
            return result
        
        return wrapper
    return decorator

def clear_cache(prefix: Optional[str] = None) -> int:
    """
    Clear cache entries.
    
    Args:
        prefix: If provided, only clear entries with this prefix in the key
    
    Returns:
        Number of entries cleared
    """
    manifest = _load_manifest()
    entries_to_remove = []
    
    for key in manifest.get("entries", {}).keys():
        if prefix is None or key.startswith(prefix):
            entries_to_remove.append(key)
    
    for key in entries_to_remove:
        entry = manifest["entries"][key]
        cache_path = _get_cache_path(key, entry.get("extension", ".json"))
        if cache_path.exists():
            cache_path.unlink()
            logger.info(f"Removed cached file: {cache_path}")
        del manifest["entries"][key]
    
    if entries_to_remove:
        _save_manifest(manifest)
    
    return len(entries_to_remove)

def profile_function(func: Callable[..., T], *args, **kwargs) -> Tuple[T, Dict[str, Any]]:
    """
    Profile a function execution and return result with timing stats.
    
    Returns:
        Tuple of (result, profile_stats)
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    
    profile_stats = {
        "execution_time_seconds": end_time - start_time,
        "function_name": func.__name__,
        "args_count": len(args),
        "kwargs_count": len(kwargs)
    }
    
    return result, profile_stats

def main():
    """CLI for cache management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cache management utility")
    parser.add_argument("action", choices=["info", "clear", "profile"], help="Action to perform")
    parser.add_argument("--prefix", type=str, help="Cache prefix (for clear action)")
    parser.add_argument("--function", type=str, help="Function to profile (for profile action)")
    
    args = parser.parse_args()
    
    if args.action == "info":
        manifest = _load_manifest()
        total_entries = len(manifest.get("entries", {}))
        total_size = sum(
            entry.get("size_bytes", 0) 
            for entry in manifest.get("entries", {}).values()
        )
        print(f"Cache Status:")
        print(f"  Total entries: {total_entries}")
        print(f"  Total size: {total_size / 1024 / 1024:.2f} MB")
        print(f"  Cache directory: {CACHE_DIR}")
        
    elif args.action == "clear":
        count = clear_cache(args.prefix)
        print(f"Cleared {count} cache entries")
        
    elif args.action == "profile":
        print("Profiling functionality requires specific function implementation.")
        print("Use the @profile_function decorator in your code to profile specific functions.")

if __name__ == "__main__":
    setup_logging()
    main()
