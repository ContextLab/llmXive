"""
Memory management utilities for the self-improving LLM pipeline.

Provides a hard RAM watchdog to enforce strict memory limits, preventing
out-of-memory crashes during training by terminating the process if limits
are exceeded.
"""
import os
import sys
import gc
import time
import psutil
from typing import Optional, Callable, Any


def get_memory_usage_gb() -> float:
    """
    Get the current RAM usage of the current process in Gigabytes.
    
    Returns:
        float: Memory usage in GB.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    # rss is Resident Set Size (physical RAM)
    return mem_info.rss / (1024 ** 3)


def check_and_terminate_if_exceeds(limit_gb: float = 7.0) -> None:
    """
    Hard RAM watchdog: checks current process memory usage and terminates
    the process if it exceeds the specified limit.
    
    This function does NOT modify training parameters, batch sizes, or
    attempt to recover. It strictly enforces the limit by killing the
    process to prevent system instability.
    
    Args:
        limit_gb (float): The maximum allowed RAM usage in Gigabytes.
                          Defaults to 7.0 GB.
    
    Raises:
        SystemExit: If memory usage exceeds the limit.
    """
    current_usage = get_memory_usage_gb()
    
    if current_usage > limit_gb:
        # Force garbage collection before final check to ensure accurate reading
        gc.collect()
        # Re-check after GC
        current_usage = get_memory_usage_gb()
        
        if current_usage > limit_gb:
            error_msg = (
                f"CRITICAL MEMORY LIMIT EXCEEDED: "
                f"Current usage {current_usage:.2f} GB > Limit {limit_gb:.2f} GB. "
                f"Terminating process to prevent system instability."
            )
            print(error_msg, file=sys.stderr)
            
            # Log a final cleanup attempt if possible, but do not block termination
            try:
                with open("data/processed/memory_termination.log", "a") as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_msg}\n")
            except Exception:
                pass
            
            # Force termination
            os._exit(1)


def enable_gradient_checkpointing(module: Any) -> None:
    """
    Enable gradient checkpointing for a given PyTorch module to save memory.
    
    Note: While this function exists for API compatibility with the broader
    pipeline, T004 strictly enforces that the watchdog ONLY terminates.
    Gradient checkpointing logic for training loops belongs in T017a.
    
    Args:
        module: A PyTorch nn.Module that supports gradient_checkpointing.
    """
    try:
        # Attempt to enable checkpointing if the module has the method
        if hasattr(module, 'gradient_checkpointing_enable'):
            module.gradient_checkpointing_enable()
    except Exception:
        # Silently ignore if the specific module doesn't support it or fails
        # The watchdog will still catch OOM if this fails to save memory
        pass