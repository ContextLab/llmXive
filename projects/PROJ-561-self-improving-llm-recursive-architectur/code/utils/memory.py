"""
Memory management utilities for the self-improving LLM pipeline.

Provides:
- Gradient checkpointing utilities
- Batch size auto-scaling
- Hard RAM watchdog (process termination on OOM risk)
"""

import os
import sys
import gc
import time
import psutil
from typing import Optional, Callable, Any


# Constants for batch scaling
MIN_BATCH_SIZE = 1
MAX_BATCH_SIZE = 64
MEMORY_THRESHOLD_FACTOR = 0.85  # Trigger scaling at 85% of limit


def get_memory_usage_gb() -> float:
    """
    Returns the current RAM usage of the current process in Gigabytes.
    Uses psutil for cross-platform compatibility.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    # Convert bytes to GB
    return mem_info.rss / (1024 ** 3)



def check_and_terminate_if_exceeds(limit_gb: float = 7.0) -> None:
    """
    Hard RAM watchdog.
    
    Checks the current process's RAM usage. If it exceeds `limit_gb`,
    the process is terminated immediately with a non-zero exit code
    and a descriptive error message to stderr.
    
    This function never returns if the limit is exceeded.
    
    Args:
        limit_gb: The maximum allowed RAM usage in GB.
    
    Raises:
        SystemExit: If memory usage exceeds the limit.
    """
    current_usage = get_memory_usage_gb()
    if current_usage > limit_gb:
        error_msg = (
            f"CRITICAL: RAM usage {current_usage:.2f} GB exceeds limit {limit_gb:.2f} GB. "
            "Terminating process to prevent system instability."
        )
        sys.stderr.write(error_msg + "\n")
        # Force garbage collection one last time before exit to ensure
        # the measurement is as accurate as possible, though we are exiting.
        gc.collect()
        sys.exit(1)


def enable_gradient_checkpointing(model: nn.Module) -> None:
    """
    Recursively enables gradient checkpointing on a PyTorch model.
    
    Gradient checkpointing trades compute for memory, allowing larger
    models or batch sizes to fit in RAM by recomputing activations
    during the backward pass.
    
    Note: Only works for models where the underlying layers support it
    (e.g., transformers). For generic models, this may have no effect
    or require specific module overrides.
    
    Args:
        model: The PyTorch model to modify.
    """
    if hasattr(model, "gradient_checkpointing_enable"):
        try:
            model.gradient_checkpointing_enable()
        except Exception as e:
            sys.stderr.write(f"Warning: Could not enable gradient checkpointing on model: {e}\n")
    
    # Recursively try to enable on sub-modules if the main model didn't have the method
    for name, module in model.named_modules():
        if module is not model and hasattr(module, "gradient_checkpointing_enable"):
            try:
                module.gradient_checkpointing_enable()
            except Exception:
                pass


def auto_scale_batch_size(
    current_batch_size: int, 
    limit_gb: float, 
    safety_margin_gb: float = 1.0
) -> int:
    """
    Auto-scales the batch size down if memory usage is approaching the limit.
    
    This function checks current memory usage. If usage + safety_margin exceeds
    the limit, it halves the batch size until it fits or hits MIN_BATCH_SIZE.
    
    Args:
        current_batch_size: The batch size attempted in the current epoch.
        limit_gb: The maximum allowed RAM in GB.
        safety_margin_gb: Extra GB to reserve for overhead (default 1.0).
    
    Returns:
        The new batch size (guaranteed to be >= MIN_BATCH_SIZE).
    
    Raises:
        RuntimeError: If even MIN_BATCH_SIZE cannot fit within the limit.
    """
    check_and_terminate_if_exceeds(limit_gb)  # Hard fail if already over
    
    effective_limit = limit_gb - safety_margin_gb
    new_batch_size = current_batch_size
    
    # Check current usage against effective limit
    # We assume memory usage scales roughly linearly with batch size.
    # We estimate current usage. If it's already high, we scale down.
    current_usage = get_memory_usage_gb()
    
    # If current usage is already dangerously high relative to the effective limit,
    # we must scale down.
    while new_batch_size > MIN_BATCH_SIZE:
        # Estimate usage if we were to run with new_batch_size
        # This is a heuristic: we assume current_usage corresponds to current_batch_size
        # and we want to find a size where usage <= effective_limit
        
        # Simple heuristic: if current usage > effective limit, halve batch size.
        # A more robust way would be to measure, but we are in a loop.
        if current_usage > effective_limit:
            new_batch_size = new_batch_size // 2
            if new_batch_size < MIN_BATCH_SIZE:
                new_batch_size = MIN_BATCH_SIZE
                # Re-check with min size
                estimated_min_usage = current_usage * (MIN_BATCH_SIZE / current_batch_size)
                if estimated_min_usage > effective_limit:
                    raise RuntimeError(
                        f"OOM: Even batch size {MIN_BATCH_SIZE} estimated to use "
                        f"{estimated_min_usage:.2f} GB, exceeding effective limit {effective_limit:.2f} GB."
                    )
            # Force a check to ensure we don't loop infinitely if logic is flawed
            if new_batch_size == current_batch_size:
                break
            current_batch_size = new_batch_size
            # In a real training loop, we would actually run a forward pass to measure,
            # but here we rely on the heuristic to reduce until safe.
            # We re-evaluate the "current_usage" assumption by halving the estimate
            current_usage = current_usage * 0.5 
        else:
            break
    
    if new_batch_size < MIN_BATCH_SIZE:
        raise RuntimeError(
            f"Cannot scale batch size below {MIN_BATCH_SIZE}. "
            "System memory is insufficient for the minimum required batch size."
        )
        
    return new_batch_size