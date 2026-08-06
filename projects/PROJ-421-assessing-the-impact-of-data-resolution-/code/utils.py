"""
Utility functions for data processing, including checksumming, retry logic, and raster operations.
"""
import os
import mmap
import hashlib
import logging
import time
import json
import random
from pathlib import Path
from typing import Optional, Callable, Any, Tuple, List
import numpy as np
import rasterio
from rasterio.windows import Window

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_file: Optional path to log file. If None, logs to console only.
        level: Logging level (default: INFO)
    """
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

class RetryError(Exception):
    """Custom exception for retry failures."""
    pass

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple = (Exception,)
) -> Callable:
    """
    Decorator for retrying a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch
    
    Returns:
        Wrapped function with retry logic
    """
    def wrapper(*args, **kwargs):
        delay = base_delay
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt == max_retries:
                    raise RetryError(f"Failed after {max_retries} retries: {e}")
                
                logging.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
                delay = min(delay * backoff_factor, max_delay)
        
        raise RetryError(f"Failed after {max_retries} retries: {last_exception}")
    
    return wrapper

def create_memory_mapped_array(
    shape: Tuple[int, ...],
    dtype: np.dtype = np.float32,
    temp_dir: Optional[str] = None
) -> np.ndarray:
    """
    Create a memory-mapped array for large datasets.
    
    Args:
        shape: Shape of the array
        dtype: Data type
        temp_dir: Directory for temporary file. If None, uses system default.
    
    Returns:
        Memory-mapped numpy array
    """
    filename = os.path.join(
        temp_dir or tempfile.gettempdir(),
        f"mmap_{int(time.time())}_{random.randint(0, 10000)}.dat"
    )
    return np.memmap(filename, dtype=dtype, mode='w+', shape=shape)

def reshape_memory_map(
    mmap_array: np.memmap,
    new_shape: Tuple[int, ...]
) -> np.memmap:
    """
    Reshape a memory-mapped array.
    
    Args:
        mmap_array: Original memory-mapped array
        new_shape: New shape for the array
    
    Returns:
        Reshaped memory-mapped array
    """
    if mmap_array.size != np.prod(new_shape):
        raise ValueError(
            f"Cannot reshape array of size {mmap_array.size} to shape {new_shape}"
        )
    return np.reshape(mmap_array, new_shape)

def get_raster_info(raster_path: str) -> dict:
    """
    Get metadata information from a raster file.
    
    Args:
        raster_path: Path to the raster file
    
    Returns:
        Dictionary containing raster metadata
    
    Raises:
        FileNotFoundError: If file doesn't exist
        rasterio.errors.RasterioIOError: If file is not a valid raster
    """
    raster_path = Path(raster_path)
    if not raster_path.exists():
        raise FileNotFoundError(f"Raster file not found: {raster_path}")
    
    with rasterio.open(raster_path) as src:
        info = {
            'width': src.width,
            'height': src.height,
            'count': src.count,
            'dtype': str(src.dtypes[0]),
            'crs': str(src.crs) if src.crs else None,
            'transform': src.transform,
            'bounds': src.bounds,
            'nodata': src.nodata
        }
    return info

def validate_raster_bounds(
    raster_path: str,
    min_width: int = 1,
    min_height: int = 1
) -> bool:
    """
    Validate that a raster has valid dimensions.
    
    Args:
        raster_path: Path to the raster file
        min_width: Minimum required width
        min_height: Minimum required height
    
    Returns:
        True if valid, False otherwise
    """
    try:
        info = get_raster_info(raster_path)
        return info['width'] >= min_width and info['height'] >= min_height
    except Exception:
        return False

def validate_raster_bounds_with_retry(
    raster_path: str,
    max_retries: int = 3
) -> bool:
    """
    Validate raster bounds with retry logic.
    
    Args:
        raster_path: Path to the raster file
        max_retries: Maximum retry attempts
    
    Returns:
        True if valid, False otherwise
    """
    @retry_with_backoff(max_retries=max_retries)
    def _validate():
        return validate_raster_bounds(raster_path)
    
    return _validate()

def iter_windows(
    width: int,
    height: int,
    window_size: int = 1024
) -> List[Window]:
    """
    Generate window coordinates for iterating over a raster.
    
    Args:
        width: Raster width
        height: Raster height
        window_size: Size of each window (default: 1024)
    
    Returns:
        List of Window objects
    """
    windows = []
    for row_off in range(0, height, window_size):
        for col_off in range(0, width, window_size):
            row_end = min(row_off + window_size, height)
            col_end = min(col_off + window_size, width)
            windows.append(
                Window(col_off, row_off, col_end - col_off, row_end - row_off)
            )
    return windows

def read_raster_windowed(
    raster_path: str,
    window: Window,
    band: int = 1
) -> np.ndarray:
    """
    Read a window of data from a raster file.
    
    Args:
        raster_path: Path to the raster file
        window: Window to read
        band: Band number (default: 1)
    
    Returns:
        NumPy array containing the window data
    """
    with rasterio.open(raster_path) as src:
        return src.read(band, window=window)

def read_raster_windowed_with_retry(
    raster_path: str,
    window: Window,
    band: int = 1,
    max_retries: int = 3
) -> np.ndarray:
    """
    Read a window of data with retry logic.
    
    Args:
        raster_path: Path to the raster file
        window: Window to read
        band: Band number (default: 1)
        max_retries: Maximum retry attempts
    
    Returns:
        NumPy array containing the window data
    """
    @retry_with_backoff(max_retries=max_retries)
    def _read():
        return read_raster_windowed(raster_path, window, band)
    
    return _read()

def checksum_file(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: 'sha256')
    
    Returns:
        Hexadecimal checksum string
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If algorithm is not supported
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    hasher = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(65536), b''):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def validate_raster_metadata(
    raster_path: str,
    expected_checksum: Optional[str] = None,
    expected_dtype: Optional[str] = None,
    expected_crs: Optional[str] = None
) -> dict:
    """
    Validate raster metadata against expected values.
    
    Args:
        raster_path: Path to the raster file
        expected_checksum: Expected file checksum (optional)
        expected_dtype: Expected data type (optional)
        expected_crs: Expected CRS (optional)
    
    Returns:
        Dictionary with validation results
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    try:
        info = get_raster_info(raster_path)
        
        if expected_checksum:
            actual_checksum = checksum_file(raster_path)
            if actual_checksum != expected_checksum:
                result['valid'] = False
                result['errors'].append(
                    f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}"
                )
        
        if expected_dtype and info['dtype'] != expected_dtype:
            result['valid'] = False
            result['errors'].append(
                f"Data type mismatch: expected {expected_dtype}, got {info['dtype']}"
            )
        
        if expected_crs and info['crs'] != expected_crs:
            result['valid'] = False
            result['errors'].append(
                f"CRS mismatch: expected {expected_crs}, got {info['crs']}"
            )
        
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Validation failed: {str(e)}")
    
    return result
