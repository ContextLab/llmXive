import logging
import json
import resource
import sys
import os
from typing import Callable, Iterable, Optional, List, Any, Iterator
import psutil

def configure_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger with JSON-formatted handlers.
    
    Args:
        log_file: Optional path to a log file. If None, logs to stderr.
    
    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    formatter = logging.Formatter(
        fmt='{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    
    if log_file:
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Always add a console handler for visibility
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def get_system_memory_limit() -> int:
    """
    Get the soft memory limit for the current process in bytes.
    
    Returns:
        Memory limit in bytes. Returns a large default if limit cannot be determined.
    """
    try:
        # resource limits are in bytes on Unix
        soft_limit, _ = resource.getrlimit(resource.RLIMIT_AS)
        if soft_limit == resource.RLIM_INFINITY or soft_limit == -1:
            # Fallback to total system memory if no limit set
            return psutil.virtual_memory().total
        return soft_limit
    except (ImportError, AttributeError):
        # Fallback for Windows or non-Unix systems
        return psutil.virtual_memory().total

def estimate_ram(df_sample: Any, rows: int) -> int:
    """
    Estimate the RAM required to load a DataFrame of a given size.
    
    Args:
        df_sample: A sample DataFrame or object with dtypes to estimate size per row.
        rows: The number of rows to estimate for.
    
    Returns:
        Estimated memory in bytes.
    """
    if df_sample is None:
        # Default estimate: 100 bytes per row (conservative for mixed types)
        return rows * 100
    
    try:
        # If it's a pandas DataFrame
        if hasattr(df_sample, 'memory_usage'):
            # Get memory usage of the sample (in bytes)
            sample_rows = len(df_sample)
            if sample_rows == 0:
                return rows * 100
            bytes_per_row = df_sample.memory_usage(deep=True).sum() / sample_rows
            return int(bytes_per_row * rows)
        else:
            # Fallback for other iterable types
            return rows * 100
    except Exception:
        return rows * 100

def process_chunked(
    data: Iterable[Any],
    processor: Callable[[List[Any]], Any],
    initial_chunk_size: int = 1000,
    max_chunk_size: int = 5000,
    min_chunk_size: int = 100,
    sample_data: Optional[Any] = None
) -> Iterator[Any]:
    """
    Process an iterable in memory-safe chunks with dynamic size adjustment.
    
    This function attempts to read and process data in chunks, adjusting the chunk
    size dynamically based on memory usage estimates. If memory estimation fails
    or the total size is unknown, it falls back to a safe batch size of <= 1000.
    
    Args:
        data: The iterable data source (e.g., a file path, generator, or list).
        processor: A callable that takes a list of items and returns processed results.
        initial_chunk_size: Starting chunk size for iteration.
        max_chunk_size: Maximum allowed chunk size.
        min_chunk_size: Minimum allowed chunk size to prevent infinite loops.
        sample_data: Optional sample data to estimate RAM usage per row.
    
    Yields:
        The result of applying the processor to each chunk.
    
    Raises:
        MemoryError: If the minimum chunk size still exceeds memory limits.
    """
    # Determine total size if possible, otherwise assume unknown
    total_size = None
    try:
        if hasattr(data, '__len__'):
            total_size = len(data)
    except Exception:
        total_size = None
    
    # Determine chunk size logic
    current_chunk_size = initial_chunk_size
    
    # Fallback constraint: if total size unknown or memory estimation unreliable,
    # enforce a hard limit of 1000 as per task requirements
    if total_size is None or sample_data is None:
        current_chunk_size = min(current_chunk_size, 1000)
    
    # Ensure we don't exceed max or go below min
    current_chunk_size = max(min_chunk_size, min(current_chunk_size, max_chunk_size))
    
    # Get system memory limit
    memory_limit = get_system_memory_limit()
    
    # Estimate memory per item if we have sample data
    # We use a conservative multiplier (0.5) to ensure we don't hit the limit
    safe_memory_threshold = int(memory_limit * 0.5)
    
    items = []
    count = 0
    
    # Convert to iterator if it isn't already
    data_iter = iter(data)
    
    while True:
        try:
            # Try to fill the current chunk
            chunk_items = []
            for _ in range(current_chunk_size):
                try:
                    item = next(data_iter)
                    chunk_items.append(item)
                except StopIteration:
                    break
            
            if not chunk_items:
                break
            
            # Estimate memory for this chunk
            # If sample_data is None, we use a conservative estimate
            estimated_chunk_memory = estimate_ram(sample_data, len(chunk_items))
            
            # If memory estimation is too high, reduce chunk size
            if estimated_chunk_memory > safe_memory_threshold:
                # Reduce chunk size by half
                new_chunk_size = current_chunk_size // 2
                if new_chunk_size < min_chunk_size:
                    raise MemoryError(
                        f"Minimum chunk size ({min_chunk_size}) still exceeds memory limit. "
                        f"Estimated need: {estimated_chunk_memory} bytes, Limit: {safe_memory_threshold} bytes."
                    )
                
                # Put the items back? No, we already consumed them.
                # Instead, we process the current small chunk and retry with smaller size
                # But since we already have the items, we just process them now.
                # The next iteration will use the smaller size.
                current_chunk_size = new_chunk_size
            
            # Process the chunk
            result = processor(chunk_items)
            yield result
            
            count += len(chunk_items)
            
            # If we successfully processed a chunk, try to increase size slightly (up to max)
            # Only if we are below the hard limit of 1000 (from the fallback logic)
            if total_size is None or sample_data is None:
                # Stay at 1000 if we are in fallback mode
                pass
            else:
                # Dynamic adjustment for known sizes
                if current_chunk_size < max_chunk_size:
                    current_chunk_size = min(max_chunk_size, current_chunk_size * 2)
            
        except StopIteration:
            break
        except MemoryError:
            raise
        except Exception as e:
            # Log the error but continue if possible, or re-raise
            logger = logging.getLogger("llmXive")
            logger.error(f"Error processing chunk: {e}")
            raise