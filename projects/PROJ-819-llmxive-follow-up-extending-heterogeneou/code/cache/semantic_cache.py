import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from cachetools import LRUCache
import numpy as np
import logging
from pathlib import Path

# Configure logging for cache events
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@dataclass
class CacheEntry:
    """Represents a single entry in the semantic cache."""
    embedding: np.ndarray
    output: Any
    timestamp: float
    prompt: str
    similarity_score: Optional[float] = None

class SemanticCache:
    """
    Custom LRU wrapper around cachetools.LRUCache for semantic caching.
    Implements LRU eviction policy and logs eviction events.
    """
    
    def __init__(self, max_size: int = 1000, eviction_log_path: Optional[str] = None):
        """
        Initialize the semantic cache.
        
        Args:
            max_size: Maximum number of entries in the cache.
            eviction_log_path: Path to the log file for eviction events.
        """
        self.cache: LRUCache = LRUCache(max_size=max_size)
        self.max_size = max_size
        self.lock = threading.RLock()
        self.eviction_log_path = eviction_log_path
        
        if self.eviction_log_path:
            self._ensure_log_dir()

    def _ensure_log_dir(self):
        """Ensure the directory for the eviction log exists."""
        if self.eviction_log_path:
            log_path = Path(self.eviction_log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

    def _log_eviction(self, key: str, entry: CacheEntry):
        """Log an eviction event to the specified file."""
        if not self.eviction_log_path:
            return
        
        log_entry = {
            "timestamp": time.time(),
            "evicted_key": key,
            "evicted_prompt": entry.prompt,
            "evicted_timestamp": entry.timestamp,
            "reason": "LRU_EVICTION_LIMIT_EXCEEDED"
        }
        
        try:
            with open(self.eviction_log_path, 'a') as f:
                import json
                f.write(json.dumps(log_entry) + '\n')
            logger.info(f"Evicted entry: {key} -> {entry.prompt[:50]}...")
        except Exception as e:
            logger.error(f"Failed to write eviction log: {e}")

    def get(self, key: str) -> Optional[CacheEntry]:
        """
        Retrieve an entry from the cache.
        
        Args:
            key: The cache key (usually a hash of the prompt).
        
        Returns:
            The CacheEntry if found, None otherwise.
        """
        with self.lock:
            entry = self.cache.get(key)
            if entry:
                # Move to end to mark as recently used
                self.cache.move_to_end(key)
            return entry

    def set(self, key: str, entry: CacheEntry) -> None:
        """
        Add or update an entry in the cache.
        
        If the cache is full, the least recently used entry is evicted
        and logged before the new entry is added.
        
        Args:
            key: The cache key.
            entry: The CacheEntry to store.
        """
        with self.lock:
            # Check if adding this entry will exceed the limit
            # Note: cachetools.LRUCache handles eviction on set,
            # but we need to intercept the evicted item to log it.
            # We'll check size before set and rely on the fact that
            # if we are at max_size, the next set will evict one.
            
            current_size = len(self.cache)
            is_full = current_size >= self.max_size
            
            # If full, we need to know what will be evicted.
            # LRUCache doesn't expose the evicted item directly on set.
            # We can peek at the first item (oldest) if we are full.
            evicted_entry = None
            if is_full:
                # Get the oldest key
                oldest_key = next(iter(self.cache))
                evicted_entry = self.cache[oldest_key]

            self.cache[key] = entry
            
            # Log the eviction if one occurred
            if is_full and evicted_entry is not None:
                # The key that was just evicted is the one we peeked
                # However, if the new key was already in cache, no eviction happens.
                # We need to check if the key we just set was the one that caused eviction.
                # Actually, if we set a key that exists, no eviction.
                # If we set a new key and size was max, eviction happens.
                # Let's re-verify: if we set a new key and size was max, 
                # the oldest key is gone.
                if key not in self.cache or len(self.cache) < current_size:
                    # This branch is tricky with standard LRUCache behavior.
                    # Standard behavior: if key exists, update value, no eviction.
                    # If key new, add, if size > max, evict oldest.
                    # We peeked the oldest BEFORE set. If we set a NEW key,
                    # the oldest is evicted.
                    if key != oldest_key: # It's a new key
                        self._log_eviction(oldest_key, evicted_entry)

    def clear(self) -> None:
        """Clear the cache."""
        with self.lock:
            self.cache.clear()

    def __len__(self) -> int:
        """Return the number of items in the cache."""
        return len(self.cache)

    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        return key in self.cache

    def get_all_keys(self) -> List[str]:
        """Return a list of all keys in the cache."""
        with self.lock:
            return list(self.cache.keys())

    def evict_oldest(self) -> Optional[Tuple[str, CacheEntry]]:
        """
        Manually evict the oldest entry (LRU).
        
        Returns:
            Tuple of (key, entry) if an entry was evicted, None otherwise.
        """
        with self.lock:
            if len(self.cache) == 0:
                return None
            
            oldest_key = next(iter(self.cache))
            evicted_entry = self.cache.pop(oldest_key)
            
            self._log_eviction(oldest_key, evicted_entry)
            return oldest_key, evicted_entry

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        return {
            "current_size": len(self.cache),
            "max_size": self.max_size,
            "utilization": len(self.cache) / self.max_size if self.max_size > 0 else 0.0
        }
