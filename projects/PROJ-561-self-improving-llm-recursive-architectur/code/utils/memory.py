"""
Memory management utilities for the self-improving LLM pipeline.

Provides gradient checkpointing, batch size auto-scaling, and a hard RAM watchdog
to enforce strict memory limits on CPU-only execution environments.
"""
import os
import sys
import gc
import time
import psutil
import torch
from typing import Optional, Callable, Any, Tuple

# Constants
GB = 1024 ** 3

def get_memory_usage_gb() -> float:
    """
    Get the current RAM usage of the current process in GB.

    Returns:
        float: Memory usage in GB.
    """
    process = psutil.Process(os.getpid())
    # RSS (Resident Set Size) is the non-swapped physical memory the process has used
    rss_bytes = process.memory_info().rss
    return rss_bytes / GB

def check_and_terminate_if_exceeds(limit_gb: float) -> None:
    """
    Check if the current process RAM usage exceeds the specified limit.
    If it does, log the error and terminate the process immediately.

    This is a hard watchdog: it does not attempt recovery, only termination.

    Args:
        limit_gb (float): The maximum allowed RAM usage in GB.

    Raises:
        SystemExit: If memory usage exceeds the limit.
    """
    current_usage = get_memory_usage_gb()
    if current_usage > limit_gb:
        error_msg = (
            f"CRITICAL: Memory usage ({current_usage:.2f} GB) exceeds limit ({limit_gb:.2f} GB). "
            f"Terminating process to prevent system instability."
        )
        print(error_msg, file=sys.stderr)
        # Force garbage collection before exit to ensure clean state logging if possible
        gc.collect()
        sys.exit(1)

def enable_gradient_checkpointing(model: torch.nn.Module) -> Optional[None]:
    """
    Enable gradient checkpointing for a model to save memory at the cost of compute.

    This is useful for training large models on limited memory. It recomputes
    activations during the backward pass instead of storing them.

    Args:
        model (torch.nn.Module): The model to enable checkpointing on.

    Returns:
        None: Returns None. Logs a warning if the model does not support checkpointing.
    """
    if not hasattr(model, 'gradient_checkpointing_enable'):
        print(f"Warning: Model type {type(model).__name__} does not support gradient checkpointing. Skipping.")
        return None

    try:
        model.gradient_checkpointing_enable()
        print("Gradient checkpointing enabled successfully.")
    except Exception as e:
        print(f"Warning: Failed to enable gradient checkpointing: {e}")
    return None

def auto_scale_batch_size(
    batch_size: int,
    min_batch_size: int = 1,
    max_batch_size: int = 64,
    limit_gb: float = 6.5,
    reduction_factor: float = 0.5
) -> int:
    """
    Attempt to auto-scale the batch size based on current memory usage.

    If memory usage is near the limit, it reduces the batch size.
    If memory usage is well below the limit, it might attempt to increase it
    (though this is less common in a hard-constraint environment).

    This function is a heuristic and does not guarantee OOM prevention during
    actual forward/backward passes, but it helps manage resources proactively.

    Args:
        batch_size (int): Current batch size.
        min_batch_size (int): Minimum allowed batch size.
        max_batch_size (int): Maximum allowed batch size.
        limit_gb (float): Memory limit in GB.
        reduction_factor (float): Factor to reduce batch size by (0.5 = halve).

    Returns:
        int: The adjusted batch size.
    """
    current_usage = get_memory_usage_gb()
    
    # If we are already over the limit, force to minimum or terminate
    if current_usage > limit_gb:
        print(f"Memory critical ({current_usage:.2f} GB > {limit_gb:.2f} GB). Forcing min batch size.")
        return min_batch_size

    # If usage is high (e.g., > 80% of limit), reduce batch size
    if current_usage > (limit_gb * 0.8):
        new_size = int(batch_size * reduction_factor)
        new_size = max(min_batch_size, new_size)
        if new_size < batch_size:
            print(f"High memory usage ({current_usage:.2f} GB). Reducing batch size from {batch_size} to {new_size}.")
            return new_size
    
    return batch_size

def run_epoch_with_memory_monitoring(
    epoch_func: Callable[[], Any],
    limit_gb: float,
    check_interval_seconds: float = 5.0
) -> Any:
    """
    Run an epoch function with periodic memory checks.

    If memory exceeds the limit during the epoch, the function will attempt
    to stop gracefully (by raising an exception or returning) and log the event.
    Note: This is a monitoring wrapper; the actual termination logic for hard
    limits is handled by `check_and_terminate_if_exceeds` which should be called
    inside the epoch loop if possible.

    Args:
        epoch_func (Callable): The function to run (the epoch loop).
        limit_gb (float): Memory limit in GB.
        check_interval_seconds (float): How often to check memory.

    Returns:
        Any: The result of epoch_func, or None if terminated.
    """
    def monitor():
        while True:
            time.sleep(check_interval_seconds)
            check_and_terminate_if_exceeds(limit_gb)

    import threading
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()

    try:
        return epoch_func()
    except SystemExit:
        print("Epoch terminated due to memory limit.")
        raise
    finally:
        # The daemon thread will die when main thread dies, but we can join if needed
        # However, for simplicity in this context, we let the daemon handle it.
        pass

class MemoryWatchdog:
    """
    A context manager or class-based watchdog for monitoring memory usage.
    """
    def __init__(self, limit_gb: float, check_interval: float = 1.0):
        self.limit_gb = limit_gb
        self.check_interval = check_interval
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def _monitor_loop(self):
        while self.running:
            time.sleep(self.check_interval)
            check_and_terminate_if_exceeds(self.limit_gb)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

def enforce_ram_limit(limit_gb: float) -> None:
    """
    A wrapper that enforces the RAM limit immediately and periodically.
    This is a convenience function that calls the check and terminates if exceeded.
    """
    check_and_terminate_if_exceeds(limit_gb)
