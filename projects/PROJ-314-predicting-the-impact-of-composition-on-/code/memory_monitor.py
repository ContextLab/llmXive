import os
import sys
import logging
import gc
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logging.warning("psutil not installed. Memory monitoring will be skipped.")

from config import get_int_config, get_project_config

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.FileHandler(Path("logs/memory_monitor.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def get_memory_usage_gb() -> float:
    """
    Get the current resident set size (RSS) memory usage in GB.
    
    Returns:
        float: Memory usage in GB. Returns 0.0 if psutil is not available.
    """
    if not HAS_PSUTIL:
        return 0.0
    
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    rss_bytes = mem_info.rss
    return rss_bytes / (1024 ** 3)

def check_memory_limit(limit_gb: Optional[int] = None) -> bool:
    """
    Check if current memory usage exceeds the configured limit.
    
    Args:
        limit_gb: Optional override for the memory limit in GB. 
                  If None, uses config.MEMORY_LIMIT_GB (default 6).
    
    Returns:
        bool: True if memory usage is within limits, False otherwise.
    
    Raises:
        MemoryError: If memory usage exceeds the limit.
    """
    if not HAS_PSUTIL:
        logger.warning("psutil not available, skipping memory limit check.")
        return True

    if limit_gb is None:
        # Try to get from config, default to 6GB if not found
        try:
            limit_gb = get_int_config("MEMORY_LIMIT_GB")
            if limit_gb is None:
                limit_gb = 6
        except Exception:
            limit_gb = 6

    current_usage = get_memory_usage_gb()
    
    log_msg = f"Current memory usage: {current_usage:.2f} GB / Limit: {limit_gb} GB"
    
    if current_usage > limit_gb:
        error_msg = f"MEMORY_LIMIT_EXCEEDED: {log_msg}"
        logger.error(error_msg)
        logger.error(f"Current memory usage: {current_usage:.2f} GB exceeds limit of {limit_gb} GB")
        raise MemoryError(error_msg)
    
    logger.info(log_msg)
    return True

def force_garbage_collection() -> None:
    """
    Force Python garbage collection to free up memory.
    """
    logger.info("Forcing garbage collection...")
    gc.collect()
    logger.info("Garbage collection complete.")
    if HAS_PSUTIL:
        logger.info(f"Memory after GC: {get_memory_usage_gb():.2f} GB")

def validate_dataset_size(
    file_path: str, 
    max_size_gb: Optional[float] = None
) -> bool:
    """
    Validate that a dataset file does not exceed the memory limit.
    
    Args:
        file_path: Path to the dataset file.
        max_size_gb: Optional override for max file size in GB.
                    Defaults to MEMORY_LIMIT_GB from config.
    
    Returns:
        bool: True if file size is acceptable, False otherwise.
    
    Raises:
        ValueError: If the file exceeds the memory limit.
    """
    if not HAS_PSUTIL:
        logger.warning("psutil not available, skipping file size validation.")
        return True

    if max_size_gb is None:
        try:
            max_size_gb = get_int_config("MEMORY_LIMIT_GB")
            if max_size_gb is None:
                max_size_gb = 6.0
        except Exception:
            max_size_gb = 6.0

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    file_size_bytes = path.stat().st_size
    file_size_gb = file_size_bytes / (1024 ** 3)

    if file_size_gb > max_size_gb:
        error_msg = f"FILE_TOO_LARGE: {file_path} ({file_size_gb:.2f} GB) exceeds limit ({max_size_gb} GB)"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"File size validation passed: {file_path} ({file_size_gb:.2f} GB)")
    return True

def main() -> None:
    """
    Main entry point for memory monitoring.
    
    This function performs a basic memory check and logs the results.
    It is intended to be called at critical points in the pipeline
    to ensure memory usage stays within bounds.
    """
    logger.info("Starting memory monitor check...")
    
    try:
        # Check current memory usage
        check_memory_limit()
        
        # Force GC to demonstrate capability
        force_garbage_collection()
        
        # Check again after GC
        check_memory_limit()
        
        logger.info("Memory monitor check completed successfully.")
        
    except MemoryError as e:
        logger.error(f"Memory check failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during memory check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
