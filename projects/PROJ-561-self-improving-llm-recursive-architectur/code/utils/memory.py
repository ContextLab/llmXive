import os
import sys
import gc
import time
import logging
import psutil
from typing import Optional

from config import get_config

# Configure logger for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def get_memory_usage_gb() -> float:
    """
    Returns the current RAM usage of the current process in GB.
    
    Returns:
        float: Memory usage in GB.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)


def check_ram_usage(limit_gb: float) -> bool:
    """
    Checks if the current RAM usage exceeds the specified limit.
    
    This function reads the limit from the provided argument (which should 
    ideally be sourced from config.py in the calling context, but is passed 
    explicitly here for flexibility). 
    
    If the current RAM usage exceeds `limit_gb`, it logs a warning with the 
    actual peak value found. It does NOT terminate the process; termination 
    is handled by other modules (e.g., T036a) per FR-015.
    
    Args:
        limit_gb (float): The maximum allowed RAM usage in GB.
        
    Returns:
        bool: True if usage exceeds the limit, False otherwise.
    """
    current_usage = get_memory_usage_gb()
    
    if current_usage > limit_gb:
        logger.warning(f"RAM Warning: {current_usage:.2f}GB")
        return True
    else:
        logger.debug(f"RAM usage {current_usage:.2f}GB is within limit {limit_gb}GB")
        return False


def check_and_terminate_if_exceeds(limit_gb: float) -> None:
    """
    Checks RAM usage and terminates the process if the limit is exceeded.
    
    This is a hard enforcement function used when strict limits must be 
    respected (e.g., CI constraints), distinct from the warning-only 
    behavior of check_ram_usage.
    
    Args:
        limit_gb (float): The maximum allowed RAM usage in GB.
        
    Raises:
        SystemExit: If memory usage exceeds the limit.
    """
    current_usage = get_memory_usage_gb()
    if current_usage > limit_gb:
        logger.critical(f"RAM limit exceeded: {current_usage:.2f}GB > {limit_gb}GB. Terminating.")
        raise SystemExit(f"RAM limit exceeded: {current_usage:.2f}GB > {limit_gb}GB")


def enable_gradient_checkpointing(model) -> None:
    """
    Enables gradient checkpointing for a PyTorch model to save memory.
    
    Args:
        model: A PyTorch nn.Module.
    """
    if hasattr(model, 'gradient_checkpointing_enable'):
        model.gradient_checkpointing_enable()
        logger.info("Gradient checkpointing enabled for model.")
    else:
        logger.warning("Model does not support gradient_checkpointing_enable.")


def auto_scale_batch_size(current_batch_size: int, limit_gb: float) -> int:
    """
    Attempts to scale down the batch size if RAM usage is too high.
    
    Args:
        current_batch_size (int): The current batch size.
        limit_gb (float): The RAM limit in GB.
        
    Returns:
        int: The new batch size (either original or reduced).
    """
    if check_ram_usage(limit_gb):
        new_bs = max(1, current_batch_size // 2)
        logger.warning(f"Reducing batch size from {current_batch_size} to {new_bs} due to RAM constraints.")
        return new_bs
    return current_batch_size


def run_epoch_with_memory_monitoring(epoch_func, limit_gb: float, *args, **kwargs):
    """
    Wrapper to run an epoch function with memory monitoring.
    
    If memory exceeds the limit during execution, it logs a warning but 
    allows the function to continue (matching the behavior of check_ram_usage).
    
    Args:
        epoch_func: The function to execute (e.g., train_epoch).
        limit_gb (float): The RAM limit in GB.
        *args: Arguments to pass to epoch_func.
        **kwargs: Keyword arguments to pass to epoch_func.
        
    Returns:
        The result of epoch_func.
    """
    logger.info(f"Starting epoch with memory limit {limit_gb}GB")
    try:
        result = epoch_func(*args, **kwargs)
        return result
    finally:
        usage = get_memory_usage_gb()
        logger.info(f"Epoch finished. Final memory usage: {usage:.2f}GB")
        if usage > limit_gb:
            logger.warning(f"Post-epoch memory usage {usage:.2f}GB exceeds limit {limit_gb}GB")


class MemoryWatchdog:
    """
    A context manager to monitor memory usage during a block of code.
    """
    def __init__(self, limit_gb: float):
        self.limit_gb = limit_gb
        self.start_usage = 0.0
        self.peak_usage = 0.0

    def __enter__(self):
        gc.collect()
        self.start_usage = get_memory_usage_gb()
        self.peak_usage = self.start_usage
        logger.info(f"MemoryWatchdog started. Initial usage: {self.start_usage:.2f}GB")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        current = get_memory_usage_gb()
        if current > self.peak_usage:
            self.peak_usage = current
        
        if self.peak_usage > self.limit_gb:
            logger.warning(f"RAM Warning: {self.peak_usage:.2f}GB (Peak during watchdog: {self.peak_usage:.2f}GB)")
        
        logger.info(f"MemoryWatchdog finished. Peak usage: {self.peak_usage:.2f}GB")
        return False


def enforce_ram_limit(limit_gb: float) -> None:
    """
    Enforces the RAM limit by terminating if exceeded.
    
    Args:
        limit_gb (float): The limit in GB.
    """
    check_and_terminate_if_exceeds(limit_gb)
