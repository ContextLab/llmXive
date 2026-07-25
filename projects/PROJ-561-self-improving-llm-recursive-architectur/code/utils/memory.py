"""
Memory management utilities for the self-improving LLM pipeline.

Provides gradient checkpointing, batch size auto-scaling, and a hard RAM watchdog
to prevent Out-Of-Memory (OOM) crashes on CPU-only environments.
"""
import os
import sys
import gc
import time
import psutil
import torch
import torch.nn as nn
from typing import Optional, Callable, Any, Tuple


def get_memory_usage_gb() -> float:
    """
    Get the current RAM usage of the current process in gigabytes.
    
    Returns:
        float: Memory usage in GB.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)


def check_and_terminate_if_exceeds(limit_gb: float) -> None:
    """
    Hard RAM watchdog: checks current memory usage and terminates the process
    if it exceeds the specified limit.
    
    This function is designed to be called periodically during training loops
    to enforce strict memory constraints (SC-005).
    
    Args:
        limit_gb (float): The maximum allowed RAM usage in gigabytes.
        
    Raises:
        SystemExit: If memory usage exceeds the limit, terminating the process.
    """
    current_gb = get_memory_usage_gb()
    if current_gb > limit_gb:
        print(f"[MEMORY WATCHDOG] CRITICAL: RAM usage {current_gb:.2f}GB exceeds limit {limit_gb:.2f}GB. Terminating process.", file=sys.stderr)
        # Force garbage collection one last time before exit attempt
        gc.collect()
        if get_memory_usage_gb() > limit_gb:
            sys.exit(1)


def enable_gradient_checkpointing(model: nn.Module) -> None:
    """
    Enable gradient checkpointing for a model to reduce memory usage.
    
    This function attempts to enable gradient checkpointing on all modules
    within the model that support it (e.g., transformers, custom modules with
    a `gradient_checkpointing_enable` method).
    
    Args:
        model (nn.Module): The model to modify.
    """
    if hasattr(model, 'gradient_checkpointing_enable'):
        try:
            model.gradient_checkpointing_enable()
            print("[MEMORY] Gradient checkpointing enabled for model.")
        except Exception as e:
            print(f"[MEMORY] Warning: Could not enable gradient checkpointing: {e}")
    else:
        # Fallback: try to set attribute if it exists but isn't a method
        if hasattr(model, 'gradient_checkpointing'):
            model.gradient_checkpointing = True
            print("[MEMORY] Gradient checkpointing enabled via attribute.")
        else:
            print("[MEMORY] Model does not support gradient checkpointing.")


def auto_scale_batch_size(
    current_batch_size: int,
    current_memory_gb: float,
    limit_gb: float,
    min_batch_size: int = 1
) -> Tuple[int, bool]:
    """
    Auto-scale batch size based on current memory usage.
    
    If current memory usage is approaching the limit, reduces the batch size
    by half. If memory is well within limits, keeps the batch size as is.
    
    Args:
        current_batch_size (int): The current batch size.
        current_memory_gb (float): Current memory usage in GB.
        limit_gb (float): The memory limit in GB.
        min_batch_size (int): Minimum allowed batch size.
        
    Returns:
        Tuple[int, bool]: (new_batch_size, was_scaled_down)
    """
    # Safety margin: if we are above 80% of the limit, scale down
    threshold = limit_gb * 0.80
    
    if current_memory_gb > threshold:
        new_batch_size = current_batch_size // 2
        if new_batch_size < min_batch_size:
            print(f"[MEMORY] CRITICAL: Batch size {current_batch_size} would drop below min {min_batch_size}. Cannot scale further. Terminating.")
            sys.exit(1)
        print(f"[MEMORY] High memory usage ({current_memory_gb:.2f}GB > {threshold:.2f}GB). Reducing batch size from {current_batch_size} to {new_batch_size}.")
        return new_batch_size, True
    
    return current_batch_size, False


def run_epoch_with_memory_monitoring(
    epoch_func: Callable[[int], Any],
    limit_gb: float,
    check_interval_seconds: float = 5.0
) -> Any:
    """
    Wrapper to run an epoch function with periodic memory checks.
    
    Args:
        epoch_func (Callable): The function to run (e.g., train_epoch).
        limit_gb (float): Memory limit in GB.
        check_interval_seconds (float): How often to check memory.
        
    Returns:
        Any: The return value of epoch_func.
    """
    import threading
    import time as time_mod
    
    stop_flag = threading.Event()
    result = [None]
    exception = [None]
    
    def monitor():
        while not stop_flag.is_set():
            try:
                check_and_terminate_if_exceeds(limit_gb)
            except SystemExit:
                raise
            time_mod.sleep(check_interval_seconds)
    
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()
    
    try:
        result[0] = epoch_func(0) # Assuming epoch_func takes epoch index
    except Exception as e:
        exception[0] = e
    finally:
        stop_flag.set()
        monitor_thread.join(timeout=1.0)
    
    if exception[0]:
        raise exception[0]
    
    return result[0]


class MemoryWatchdog:
    """
    A context manager and utility class for memory monitoring.
    """
    def __init__(self, limit_gb: float):
        self.limit_gb = limit_gb
        self.start_gb = 0.0
        self.peak_gb = 0.0
    
    def __enter__(self):
        gc.collect()
        self.start_gb = get_memory_usage_gb()
        self.peak_gb = self.start_gb
        print(f"[MEMORY WATCHDOG] Started. Limit: {self.limit_gb}GB, Start: {self.start_gb:.2f}GB")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        current = get_memory_usage_gb()
        self.peak_gb = max(self.peak_gb, current)
        print(f"[MEMORY WATCHDOG] Finished. Peak: {self.peak_gb:.2f}GB")
        check_and_terminate_if_exceeds(self.limit_gb)
        return False
    
    def check(self) -> bool:
        """
        Check current memory and update peak. Returns True if safe.
        """
        current = get_memory_usage_gb()
        self.peak_gb = max(self.peak_gb, current)
        if current > self.limit_gb:
            print(f"[MEMORY WATCHDOG] EXCEEDED: {current:.2f}GB > {self.limit_gb}GB")
            return False
        return True


def enforce_ram_limit(limit_gb: float) -> None:
    """
    Immediate enforcement of RAM limit. Checks once and exits if exceeded.
    """
    check_and_terminate_if_exceeds(limit_gb)