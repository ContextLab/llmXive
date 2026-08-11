import os
import sys
import logging
import gc
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import psutil
except ImportError:
    raise ImportError(
        "psutil is required for memory monitoring. "
        "Install it via: pip install psutil"
    )

# Import project configuration utilities
from config import get_int_config, initialize_config, load_environment

# Ensure logging is initialized
from code import logger

MEMORY_LIMIT_GB = 6  # Default fallback if config is missing

def get_memory_usage_gb() -> float:
    """
    Get the current Resident Set Size (RSS) memory usage of the current process in GB.
    
    Returns:
        float: Memory usage in GB.
    """
    process = psutil.Process(os.getpid())
    # mem_info = process.memory_info()
    # rss is in bytes
    rss_bytes = process.memory_info().rss
    return rss_bytes / (1024 ** 3)

def check_memory_limit(limit_gb: Optional[float] = None) -> bool:
    """
    Check if the current memory usage exceeds the specified limit.
    
    Args:
        limit_gb (float, optional): The memory limit in GB. Defaults to config.MEMORY_LIMIT_GB or 6GB.
        
    Returns:
        bool: True if memory usage is within limits, False otherwise.
        
    Raises:
        MemoryError: If memory usage exceeds the limit.
    """
    if limit_gb is None:
        # Try to get from config, fallback to default
        try:
            # Ensure config is loaded
            load_environment()
            initialize_config()
            limit_gb = get_int_config("MEMORY_LIMIT_GB", default=6)
        except Exception:
            limit_gb = MEMORY_LIMIT_GB

    current_usage = get_memory_usage_gb()
    
    if current_usage > limit_gb:
        error_msg = (
            f"Memory limit exceeded: Current usage {current_usage:.2f} GB "
            f"exceeds limit {limit_gb} GB"
        )
        logger.error(error_msg)
        raise MemoryError(error_msg)
    
    logger.debug(f"Memory check passed: {current_usage:.2f} GB / {limit_gb} GB")
    return True

def force_garbage_collection() -> None:
    """
    Force Python garbage collection to free up unused memory.
    """
    gc.collect()
    logger.debug("Garbage collection triggered")

def validate_dataset_size(df: Any, limit_gb: Optional[float] = None) -> bool:
    """
    Estimate the memory usage of a pandas DataFrame and check against limit.
    
    Args:
        df: A pandas DataFrame object.
        limit_gb (float, optional): The memory limit in GB.
        
    Returns:
        bool: True if estimated size is within limits, False otherwise.
        
    Raises:
        MemoryError: If estimated size exceeds the limit.
    """
    if hasattr(df, 'memory_usage'):
        # Estimate total memory usage in bytes
        estimated_bytes = df.memory_usage(deep=True).sum()
        estimated_gb = estimated_bytes / (1024 ** 3)
    else:
        estimated_gb = 0
        logger.warning("Input object does not have memory_usage method, skipping size check")
        return True

    if limit_gb is None:
        try:
            load_environment()
            initialize_config()
            limit_gb = get_int_config("MEMORY_LIMIT_GB", default=6)
        except Exception:
            limit_gb = MEMORY_LIMIT_GB

    if estimated_gb > limit_gb:
        error_msg = (
            f"Dataset size validation failed: Estimated size {estimated_gb:.2f} GB "
            f"exceeds limit {limit_gb} GB"
        )
        logger.error(error_msg)
        raise MemoryError(error_msg)

    logger.info(f"Dataset size check passed: {estimated_gb:.2f} GB / {limit_gb} GB")
    return True

def log_memory_usage(message: str = "Memory Usage Check") -> Dict[str, float]:
    """
    Log the current memory usage and return the metrics.
    
    Args:
        message (str): A descriptive message for the log entry.
        
    Returns:
        dict: A dictionary containing current memory usage metrics.
    """
    current_gb = get_memory_usage_gb()
    log_entry = {
        "message": message,
        "current_memory_gb": current_gb,
        "limit_gb": get_int_config("MEMORY_LIMIT_GB", default=6)
    }
    
    log_line = f"{message}: Current memory usage = {current_gb:.2f} GB"
    logger.info(log_line)
    
    # Also write to a specific memory monitor log file if needed
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    memory_log_path = logs_dir / "memory_monitor.log"
    with open(memory_log_path, "a") as f:
        f.write(f"{log_line}\n")
        
    return log_entry

def main() -> None:
    """
    Main entry point for memory monitoring checks.
    This function performs a basic check and logs the results.
    It can be called by other pipeline stages to enforce memory constraints.
    """
    logger.info("Starting memory monitor check...")
    
    try:
        # Force garbage collection before checking
        force_garbage_collection()
        
        # Check current memory usage
        log_memory_usage("Initial Check")
        
        # Check against limit (raises MemoryError if exceeded)
        check_memory_limit()
        
        logger.info("Memory check completed successfully.")
        
    except MemoryError as e:
        logger.critical(f"Memory check failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during memory check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()