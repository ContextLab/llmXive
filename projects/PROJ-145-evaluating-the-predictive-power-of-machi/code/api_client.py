"""
Local Proxy Client for AFLOW Thermodynamics dataset.
Provides a fast lookup interface to verify composition existence in the local dataset.
"""
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
from config import DATA_RAW

logger = logging.getLogger(__name__)

# Global cache for the proxy index to avoid reloading on every call
_proxy_index: Optional[set] = None
_proxy_df: Optional[pd.DataFrame] = None

# Simulated rate limit configuration
_RATE_LIMIT_DELAY = 0.0  # seconds (set > 0 to simulate rate limiting)
_LAST_CALL_TIME = 0.0

def _load_proxy_data() -> set:
    """
    Loads the local proxy dataset from disk and builds a set of composition strings.
    This is called lazily on the first invocation of query_local_proxy.
    """
    global _proxy_index, _proxy_df
    if _proxy_index is not None:
        return _proxy_index

    raw_path = DATA_RAW / "aflow_raw.parquet"
    if not raw_path.exists():
        raise FileNotFoundError(
            f"Local proxy data not found at {raw_path}. "
            "Please run data_ingestion.py (T017a) first to download the dataset."
        )

    logger.info(f"Loading local proxy data from {raw_path}...")
    try:
        # Load the parquet file
        _proxy_df = pd.read_parquet(raw_path)
        
        # Validate required column exists (assumed 'composition_string' based on T012/T019c)
        if 'composition_string' not in _proxy_df.columns:
            raise ValueError(
                f"Expected column 'composition_string' not found in {raw_path}. "
                f"Available columns: {_proxy_df.columns.tolist()}"
            )
        
        # Build the set for O(1) lookup
        _proxy_index = set(_proxy_df['composition_string'].astype(str))
        logger.info(f"Loaded {len(_proxy_index)} unique compositions into local proxy index.")
        return _proxy_index
    except Exception as e:
        logger.error(f"Failed to load proxy data: {e}")
        raise

def query_local_proxy(composition_string: str) -> Dict[str, Any]:
    """
    Queries the local proxy dataset to check if a composition exists.
    
    Args:
        composition_string: A string representation of the composition (e.g., "AlFeNiCoCr").
        
    Returns:
        A dictionary with 'status' ("Found" or "Not Found") and optionally 'data'.
    """
    global _LAST_CALL_TIME
    
    # Simulated rate limit handling
    current_time = time.time()
    if current_time - _LAST_CALL_TIME < _RATE_LIMIT_DELAY:
        time.sleep(_RATE_LIMIT_DELAY - (current_time - _LAST_CALL_TIME))
    _LAST_CALL_TIME = time.time()

    index = _load_proxy_data()
    comp_str = str(composition_string)
    
    if comp_str in index:
        # If found, we could return data, but for T015 we only need existence.
        # Returning minimal payload for speed.
        return {"status": "Found", "data": None}
    else:
        return {"status": "Not Found", "data": None}

def clear_proxy_cache():
    """
    Clears the cached proxy index. Useful for testing or if the underlying file changes.
    """
    global _proxy_index, _proxy_df
    _proxy_index = None
    _proxy_df = None
    logger.info("Cleared local proxy cache.")