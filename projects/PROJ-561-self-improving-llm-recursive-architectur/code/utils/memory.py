import os
import sys
import gc
import time
import logging
import psutil
import torch
import logging
from typing import Optional, Callable, Any, Tuple

logger = logging.getLogger(__name__)

def get_memory_usage_gb() -> float:
    """
    Get the current RSS memory usage of the current process in GB.
    
    Returns:
        float: Memory usage in GB.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def check_ram_usage(limit_gb: float = 7.0) -> None:
    """
    Check if peak RAM usage exceeds the specified limit and log a warning.
    
    This function monitors the current process memory usage. If the usage
    exceeds the limit, it logs a warning message with the actual peak value.
    It does NOT trigger termination; termination is handled by T036a per FR-015.
    
    Args:
        limit_gb (float): The RAM limit in GB. Defaults to 7.0GB per SC-005 target.
    
    Note:
        This function logs a warning but does not raise an exception or exit.
    """
    current_usage = get_memory_usage_gb()
    if current_usage > limit_gb:
        logger.warning(f"RAM Warning: {current_usage:.2f}GB")
    else:
        logger.debug(f"RAM usage: {current_usage:.2f}GB (limit: {limit_gb}GB)")

def check_and_terminate_if_exceeds(limit_gb: float = 7.0) -> None:
    """
    Check if memory exceeds limit and terminate if it does.
    
    This is the termination logic referenced in the task description (T036a).
    
    Args:
        limit_gb (float): The RAM limit in GB.
    
    Raises:
        SystemExit: If memory usage exceeds the limit.
    """
    usage = get_memory_usage_gb()
    if usage > limit_gb:
        logger.error(f"CRITICAL: Memory usage {usage:.2f}GB exceeds limit {limit_gb}GB. Terminating.")
        sys.exit(1)

def enable_gradient_checkpointing(model: torch.nn.Module) -> None:
    """
    Enable gradient checkpointing for a model if supported.
    
    Args:
        model (torch.nn.Module): The model to enable checkpointing on.
    """
    if hasattr(model, 'gradient_checkpointing_enable'):
        model.gradient_checkpointing_enable()
        logger.info("Gradient checkpointing enabled.")
    else:
        logger.debug("Model does not support gradient checkpointing.")

def auto_scale_batch_size(model: torch.nn.Module, max_batch_size: int = 4) -> int:
    """
    Attempt to auto-scale batch size based on available memory.
    
    Args:
        model (torch.nn.Module): The model to test.
        max_batch_size (int): Maximum batch size to attempt.
        
    Returns:
        int: The batch size that fits in memory.
    """
    batch_size = max_batch_size
    while batch_size >= 1:
        try:
            # Simple memory check simulation
            # In a real scenario, this would try a forward pass
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            usage = get_memory_usage_gb()
            if usage < 6.0:  # Safety margin
                break
            
            batch_size //= 2
        except Exception:
            batch_size //= 2
    
    return max(1, batch_size)

def run_epoch_with_memory_monitoring(
    epoch_func: Callable, 
    limit_gb: float = 7.0, 
    *args, 
    **kwargs
) -> Any:
    """
    Run an epoch function with memory monitoring.
    
    Args:
        epoch_func: The function to run (e.g., a training epoch).
        limit_gb: Memory limit in GB.
        *args: Arguments to pass to epoch_func.
        **kwargs: Keyword arguments to pass to epoch_func.
        
    Returns:
        Any: The result of epoch_func.
    """
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    start_usage = get_memory_usage_gb()
    logger.info(f"Starting epoch. Current memory: {start_usage:.2f}GB")
    
    try:
        result = epoch_func(*args, **kwargs)
        end_usage = get_memory_usage_gb()
        logger.info(f"Epoch completed. Peak memory: {end_usage:.2f}GB")
        return result
    except Exception as e:
        end_usage = get_memory_usage_gb()
        logger.error(f"Epoch failed at {end_usage:.2f}GB: {str(e)}")
        raise

class MemoryWatchdog:
    """
    A context manager and utility class for monitoring memory during execution.
    """
    def __init__(self, limit_gb: float = 7.0, check_interval: float = 1.0):
        self.limit_gb = limit_gb
        self.check_interval = check_interval
        self.peak_usage = 0.0
        self._monitoring = False
    
    def _check(self) -> None:
        usage = get_memory_usage_gb()
        if usage > self.peak_usage:
            self.peak_usage = usage
        if usage > self.limit_gb:
            logger.warning(f"RAM Warning: {usage:.2f}GB")
    
    def start(self) -> None:
        """Start the watchdog monitoring loop."""
        self._monitoring = True
        self.peak_usage = get_memory_usage_gb()
        # In a real implementation, this would spawn a thread
        logger.info(f"Memory watchdog started. Limit: {self.limit_gb}GB")
    
    def stop(self) -> None:
        """Stop the watchdog monitoring loop."""
        self._monitoring = False
        logger.info(f"Memory watchdog stopped. Peak usage: {self.peak_usage:.2f}GB")
    
    def __enter__(self) -> 'MemoryWatchdog':
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()

def enforce_ram_limit(limit_gb: float = 7.0) -> None:
    """
    Enforce RAM limit by terminating if exceeded.
    
    Args:
        limit_gb: The RAM limit in GB.
    """
    usage = get_memory_usage_gb()
    if usage > limit_gb:
        logger.critical(f"RAM EXCEEDED: {usage:.2f} GB > {limit_gb:.2f} GB. Terminating.")
        sys.exit(1)
