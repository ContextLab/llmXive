import os
import sys
import psutil
import logging
import json
from typing import Optional
from pathlib import Path

from utils.logger import log_generation_error, get_memory_log_path, initialize_memory_log

# Default threshold: 80% of available RAM (adjustable via environment or config)
DEFAULT_MEMORY_THRESHOLD_PERCENT = 80.0

logger = logging.getLogger(__name__)

def get_available_memory_gb() -> float:
    """
    Returns the total available system memory in GB.
    """
    mem_info = psutil.virtual_memory()
    return mem_info.total / (1024 ** 3)

def get_current_memory_usage_gb() -> float:
    """
    Returns the current memory usage of the Python process in GB.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def get_memory_usage_percent() -> float:
    """
    Returns the percentage of total system memory currently used by the process.
    """
    process = psutil.Process(os.getpid())
    return process.memory_percent()

def check_memory_threshold(threshold_percent: Optional[float] = None) -> bool:
    """
    Checks if current memory usage exceeds the threshold.
    Returns True if threshold is exceeded, False otherwise.
    """
    if threshold_percent is None:
        threshold_percent = DEFAULT_MEMORY_THRESHOLD_PERCENT

    current_percent = get_memory_usage_percent()
    logger.debug(f"Current memory usage: {current_percent:.2f}% (Threshold: {threshold_percent}%)")
    
    if current_percent > threshold_percent:
        logger.warning(f"Memory usage ({current_percent:.2f}%) exceeds threshold ({threshold_percent}%)")
        return True
    return False

def log_memory_state() -> None:
    """
    Logs the current memory state to the memory log file and logger.
    """
    current_gb = get_current_memory_usage_gb()
    total_gb = get_available_memory_gb()
    percent = get_memory_usage_percent()
    
    log_entry = {
        "timestamp": str(__import__('datetime').datetime.now()),
        "current_memory_gb": round(current_gb, 3),
        "total_memory_gb": round(total_gb, 3),
        "usage_percent": round(percent, 2)
    }
    
    logger.info(f"Memory State: {log_entry}")
    
    # Append to memory log JSON file
    log_path = get_memory_log_path()
    try:
        # Ensure log directory exists
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing logs if file exists
        existing_logs = []
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r') as f:
                    existing_logs = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing_logs = []
        
        existing_logs.append(log_entry)
        
        # Write back
        with open(log_path, 'w') as f:
            json.dump(existing_logs, f, indent=2)
            
    except Exception as e:
        logger.error(f"Failed to write to memory log: {e}")

def enforce_memory_safety(threshold_percent: Optional[float] = None) -> None:
    """
    Checks memory usage and raises MemoryError if threshold is exceeded.
    This prevents OOM crashes that corrupt partial artifacts.
    
    Args:
        threshold_percent: Optional override for the memory threshold (0-100).
        
    Raises:
        MemoryError: If memory usage exceeds the threshold.
    """
    if check_memory_threshold(threshold_percent):
        current_gb = get_current_memory_usage_gb()
        total_gb = get_available_memory_gb()
        percent = get_memory_usage_percent()
        
        error_msg = (
            f"Memory safety check failed: Process usage {percent:.2f}% "
            f"({current_gb:.2f}GB / {total_gb:.2f}GB) exceeds threshold {DEFAULT_MEMORY_THRESHOLD_PERCENT}%. "
            "Initiating graceful shutdown to prevent artifact corruption."
        )
        
        # Log the error before raising
        log_generation_error(error_msg)
        
        # Raise MemoryError to trigger graceful shutdown
        raise MemoryError(error_msg)

def run_memory_monitor_pipeline(threshold_percent: Optional[float] = None) -> None:
    """
    Main entry point for memory monitoring during generation phase.
    Checks memory and logs state. Raises MemoryError if unsafe.
    
    Args:
        threshold_percent: Optional threshold override.
    """
    try:
        # Initialize logger if not done
        initialize_memory_log()
        
        # Log current state
        log_memory_state()
        
        # Enforce safety
        enforce_memory_safety(threshold_percent)
        
        logger.info("Memory check passed. Pipeline can proceed.")
        
    except MemoryError:
        # Re-raise to stop pipeline
        raise
    except Exception as e:
        logger.error(f"Memory monitoring pipeline failed: {e}")
        # Log but don't crash on monitoring failure, let pipeline continue
        # unless it's a MemoryError