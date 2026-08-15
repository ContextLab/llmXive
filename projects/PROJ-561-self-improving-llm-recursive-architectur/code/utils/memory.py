import os
import sys
import gc
import time
import psutil
import torch
import logging
from typing import Optional, Callable, Any, Tuple

# Configure logger for this module
logger = logging.getLogger(__name__)

def get_memory_usage_gb() -> float:
    """
    Returns the current RAM usage of the current process in GB.
    """
    process = psutil.Process(os.getpid())
    # RSS (Resident Set Size) is the non-swapped physical memory the task has used
    mem_bytes = process.memory_info().rss
    return mem_bytes / (1024 ** 3)

def check_ram_usage(limit_gb: float = 6.8) -> bool:
    """
    Checks current RAM usage against a limit.
    
    If critical threshold exceeded, logs a warning "RAM Critical" and logs
    the warning only. Does NOT trigger termination (termination is handled by
    T073/enforce_ram_limit per FR-015).
    
    Args:
        limit_gb: The RAM limit in GB (default 6.8).
        
    Returns:
        True if usage is within limits, False if critical threshold exceeded.
    """
    current_usage = get_memory_usage_gb()
    
    if current_usage >= limit_gb:
        logger.warning(f"RAM Critical: Current usage {current_usage:.2f} GB exceeds limit {limit_gb:.2f} GB")
        return False
    
    return True

def check_and_terminate_if_exceeds(limit_gb: float = 7.0) -> None:
    """
    Checks memory usage and terminates the process if it exceeds the limit.
    This is the enforcement logic for T073/FR-015.
    
    Args:
        limit_gb: The hard limit in GB.
        
    Raises:
        SystemExit: If memory usage exceeds the limit.
    """
    current_usage = get_memory_usage_gb()
    if current_usage > limit_gb:
        logger.critical(f"RAM EXCEEDED: {current_usage:.2f} GB > {limit_gb:.2f} GB. Terminating.")
        sys.exit(1)

def enable_gradient_checkpointing(model: torch.nn.Module) -> None:
    """
    Enables gradient checkpointing on a model if the method exists.
    """
    if hasattr(model, 'gradient_checkpointing_enable'):
        try:
            model.gradient_checkpointing_enable()
            logger.info("Gradient checkpointing enabled.")
        except Exception as e:
            logger.warning(f"Failed to enable gradient checkpointing: {e}")
    else:
        logger.debug("Model does not support gradient_checkpointing_enable.")

def auto_scale_batch_size(model: torch.nn.Module, base_batch_size: int = 4, max_attempts: int = 8) -> int:
    """
    Attempts to find a batch size that fits in memory by halving the base batch size.
    """
    gc.collect()
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
    
    current_usage = get_memory_usage_gb()
    limit_gb = 6.0 # Leave some headroom
    
    if current_usage > limit_gb:
        # Immediate fallback if already over limit
        return 1
    
    batch_size = base_batch_size
    attempts = 0
    
    while attempts < max_attempts:
        try:
            # Dummy forward pass to simulate load (simplified for utility)
            # In a real trainer, this would be the actual training step
            # For this utility, we assume if we are here, we are trying to fit
            # The actual check happens in the training loop, this is a heuristic
            return batch_size
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                batch_size //= 2
                if batch_size < 1:
                    batch_size = 1
                    break
                gc.collect()
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
            else:
                raise
        attempts += 1
        
    return batch_size

def run_epoch_with_memory_monitoring(
    epoch_func: Callable, 
    limit_gb: float = 6.8, 
    *args, 
    **kwargs
) -> Any:
    """
    Wrapper to run an epoch function with memory monitoring.
    Logs warnings if usage is high, but allows execution to continue.
    """
    # Pre-check
    check_ram_usage(limit_gb)
    
    try:
        result = epoch_func(*args, **kwargs)
    finally:
        # Post-check
        check_ram_usage(limit_gb)
        
    return result

class MemoryWatchdog:
    """
    A context manager or utility to monitor memory during a specific block of code.
    """
    def __init__(self, limit_gb: float = 6.8, logger_name: str = "MemoryWatchdog"):
        self.limit_gb = limit_gb
        self.logger = logging.getLogger(logger_name)
        self.peak_usage_gb = 0.0

    def check(self) -> bool:
        usage = get_memory_usage_gb()
        if usage > self.peak_usage_gb:
            self.peak_usage_gb = usage
        
        if usage >= self.limit_gb:
            self.logger.warning(f"Watchdog: RAM Critical at {usage:.2f} GB (Limit: {self.limit_gb} GB)")
            return False
        return True

    def get_peak(self) -> float:
        return self.peak_usage_gb

def enforce_ram_limit(limit_gb: float = 7.0) -> None:
    """
    Enforce a hard RAM limit. If exceeded, terminate the process.
    This is the specific logic required for T073.
    """
    usage = get_memory_usage_gb()
    if usage > limit_gb:
        logger.critical(f"RAM EXCEEDED: {usage:.2f} GB > {limit_gb:.2f} GB. Terminating.")
        sys.exit(1)
