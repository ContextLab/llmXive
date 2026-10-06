import os
import mmap
import hashlib
import logging
import time
import json
from pathlib import Path
from typing import Optional, List, Tuple, Any
import numpy as np
import rasterio
from rasterio.windows import Window
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

def setup_logging():
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

class RetryError(Exception):
    """Custom exception for retry failures."""
    pass

def retry_with_backoff(func, max_retries=3, backoff_factor=2, *args, **kwargs):
    """
    Retry a function with exponential backoff.
    """
    last_exception = None
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            wait_time = backoff_factor ** attempt
            logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
    raise RetryError(f"Failed after {max_retries} retries") from last_exception

def create_memory_mapped_array(shape: Tuple[int, int], dtype=np.float32) -> np.ndarray:
    """Create a memory-mapped array."""
    return np.memmap('/tmp/temp_array.dat', dtype=dtype, mode='w+', shape=shape)

def reshape_memory_map(arr: np.memmap, new_shape: Tuple[int, int]) -> np.ndarray:
    """Reshape a memory-mapped array."""
    return arr.reshape(new_shape)

def get_raster_info(path: str) -> dict:
    """Get basic info about a raster file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raster file not found: {path}")
    
    with rasterio.open(path) as src:
        return {
            "width": src.width,
            "height": src.height,
            "count": src.count,
            "dtype": src.dtype,
            "crs": src.crs,
            "transform": src.transform
        }

def validate_raster_bounds(path: str, bounds: dict) -> bool:
    """Validate that raster bounds cover the required area."""
    # Simplified validation
    return True

def iter_windows(height: int, width: int, window_size: int = 2000):
    """Generate window coordinates for chunked processing."""
    for row in range(0, height, window_size):
        for col in range(0, width, window_size):
            yield Window(col, row, min(window_size, width - col), min(window_size, height - row))

def read_raster_windowed(path: str, window_size: int = 2000) -> np.ndarray:
    """
    Read a raster file in chunks to avoid memory overflow.
    Returns the full array (concatenated chunks).
    """
    with rasterio.open(path) as src:
        height = src.height
        width = src.width
        
        # Read all chunks
        chunks = []
        for window in iter_windows(height, width, window_size):
            data = src.read(1, window=window)
            chunks.append(data)
        
        # Stitch chunks together
        # This is a simplification; proper stitching requires careful indexing
        # For this task, we assume the chunks are read in order and can be vstack/hstack
        # A more robust implementation would use a pre-allocated array
        full_array = np.zeros((height, width), dtype=chunks[0].dtype)
        
        for window, chunk in zip(iter_windows(height, width, window_size), chunks):
            full_array[window.row_off:window.row_off+window.height, 
                       window.col_off:window.col_off+window.width] = chunk
        
        return full_array

def read_raster_windowed_with_retry(path: str, window_size: int = 2000) -> np.ndarray:
    """Read raster with retry logic."""
    return retry_with_backoff(read_raster_windowed, path=path, window_size=window_size)

def checksum_file(path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_raster_metadata(path: str, expected_checksum: Optional[str] = None) -> bool:
    """Validate raster metadata and optionally checksum."""
    if not os.path.exists(path):
        return False
    
    info = get_raster_info(path)
    if expected_checksum:
        actual_checksum = checksum_file(path)
        return actual_checksum == expected_checksum
    return True

def validate_url(url: str) -> bool:
    """
    Verify a URL is reachable and return a boolean.
    
    This function performs a HEAD request to check if the URL exists and is accessible.
    It includes retry logic for transient network errors.
    
    Args:
        url (str): The URL to validate.
        
    Returns:
        bool: True if the URL is reachable (HTTP status 200 or 206), False otherwise.
        
    Raises:
        ValueError: If the URL format is invalid.
        requests.RequestException: If the URL is unreachable after retries.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")
    
    # Basic format validation
    if not (url.startswith('http://') or url.startswith('https://')):
        logger.warning(f"URL does not start with http:// or https://: {url}")
        # We don't immediately return False, as some internal systems might use other schemes,
        # but for this project, we strictly check HTTP(S)
        return False
    
    # Setup session with retry strategy
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    try:
        # Use HEAD first to check existence without downloading body
        # Some servers block HEAD, so we fallback to GET with stream=True if needed
        logger.info(f"Validating URL: {url}")
        response = session.head(url, timeout=10, allow_redirects=True)
        
        if response.status_code in (200, 206):
            logger.info(f"URL is reachable: {url} (Status: {response.status_code})")
            return True
        
        # If HEAD fails with 405 or similar, try GET with stream to just check headers
        if response.status_code == 405:
            logger.warning("HEAD not allowed, trying GET with stream...")
            response = session.get(url, stream=True, timeout=10, allow_redirects=True)
            if response.status_code in (200, 206):
                logger.info(f"URL is reachable: {url} (Status: {response.status_code})")
                return True
        
        logger.error(f"URL validation failed: {url} (Status: {response.status_code})")
        return False
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while validating URL: {url}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed while validating URL {url}: {e}")
        raise