import os
import mmap
import hashlib
import logging
import time
import json
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure root logger and return a logger instance."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance by name."""
    return logging.getLogger(name)

class RetryError(Exception):
    """Custom exception for retry failures."""
    pass

def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying a function with exponential backoff."""
    def wrapper(*args, **kwargs):
        delay = base_delay
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RetryError(f"Failed after {max_retries} attempts: {e}")
                logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
    return wrapper

def create_memory_mapped_array(file_path: Path, dtype: str = "float32", shape: Tuple[int, int] = None) -> np.ndarray:
    """Create a memory-mapped array from a binary file."""
    import numpy as np
    if not shape:
        raise ValueError("Shape must be provided for memory mapping.")
    return np.memmap(file_path, dtype=dtype, mode='r', shape=shape)

def reshape_memory_map(memmap_arr: np.ndarray, new_shape: Tuple[int, int]) -> np.ndarray:
    """Reshape a memory-mapped array."""
    return memmap_arr.reshape(new_shape)

def get_raster_info(raster_path: Path) -> Dict[str, Any]:
    """Get basic info about a raster file."""
    import rasterio
    with rasterio.open(raster_path) as src:
        return {
            "width": src.width,
            "height": src.height,
            "crs": src.crs,
            "dtype": src.dtypes[0],
            "count": src.count
        }

def validate_raster_bounds(raster_path: Path, bounds: Tuple[float, float, float, float]) -> bool:
    """Validate that raster bounds match expected bounds."""
    import rasterio
    with rasterio.open(raster_path) as src:
        src_bounds = src.bounds
        return (
            abs(src_bounds.left - bounds[0]) < 1e-6 and
            abs(src_bounds.bottom - bounds[1]) < 1e-6 and
            abs(src_bounds.right - bounds[2]) < 1e-6 and
            abs(src_bounds.top - bounds[3]) < 1e-6
        )

def validate_raster_bounds_with_retry(raster_path: Path, bounds: Tuple[float, float, float, float]) -> bool:
    """Validate raster bounds with retry logic."""
    @retry_with_backoff()
    def _validate():
        return validate_raster_bounds(raster_path, bounds)
    return _validate()

def iter_windows(height: int, width: int, window_size: int = 1024):
    """Generate window coordinates for chunked processing."""
    for row_start in range(0, height, window_size):
        for col_start in range(0, width, window_size):
            row_end = min(row_start + window_size, height)
            col_end = min(col_start + window_size, width)
            yield (row_start, row_end, col_start, col_end)

def read_raster_windowed(raster_path: Path, window: Tuple[int, int, int, int]) -> np.ndarray:
    """Read a specific window from a raster file."""
    import rasterio
    from rasterio.windows import Window
    with rasterio.open(raster_path) as src:
        row_start, row_end, col_start, col_end = window
        window_obj = Window(col_start, row_start, col_end - col_start, row_end - row_start)
        return src.read(1, window=window_obj)

def read_raster_windowed_with_retry(raster_path: Path, window: Tuple[int, int, int, int]) -> np.ndarray:
    """Read a raster window with retry logic."""
    @retry_with_backoff()
    def _read():
        return read_raster_windowed(raster_path, window)
    return _read()

def checksum_file(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate the checksum of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def validate_raster_metadata(raster_path: Path, expected_metadata: Dict[str, Any]) -> bool:
    """Validate raster metadata against expected values."""
    info = get_raster_info(raster_path)
    for key, expected_val in expected_metadata.items():
        if key not in info or info[key] != expected_val:
            return False
    return True
