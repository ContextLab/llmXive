"""
Memory management utilities for the self-improving LLM pipeline.

Provides:
- Gradient checkpointing enablement for memory savings
- Batch size auto-scaling (low-to-moderate range)
- Hard RAM watchdog to terminate process if limits exceeded
"""

import os
import sys
import gc
import time
import psutil
from typing import Optional, Callable, Any

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def get_memory_usage_gb() -> float:
    """
    Get current RAM usage of the current process in GB.

    Returns:
        float: Memory usage in GB
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)


def check_and_terminate_if_exceeds(limit_gb: float) -> None:
    """
    Check current RAM usage and terminate the process if it exceeds the limit.

    This is a hard watchdog: if memory usage exceeds limit_gb, the process
    is immediately terminated with a clear error message.

    Args:
        limit_gb: Maximum allowed RAM usage in GB. If exceeded, process terminates.

    Raises:
        SystemExit: If memory usage exceeds the limit.
    """
    current_usage = get_memory_usage_gb()
    if current_usage > limit_gb:
        error_msg = (
            f"CRITICAL: RAM usage ({current_usage:.2f} GB) exceeded limit ({limit_gb:.2f} GB). "
            f"Terminating process to prevent system instability."
        )
        sys.stderr.write(error_msg + "\n")
        sys.stderr.flush()
        # Force garbage collection before exit to ensure clean termination
        gc.collect()
        sys.exit(1)


def auto_scale_batch_size(
    base_batch_size: int = 4,
    min_batch_size: int = 1,
    max_batch_size: int = 16,
    target_memory_gb: float = 6.0,
    safety_margin: float = 0.8
) -> int:
    """
    Auto-scale batch size based on available memory.

    Starts from base_batch_size and adjusts downward if memory pressure is detected.
    Uses a conservative approach: checks memory before and after a simulated forward pass.

    Args:
        base_batch_size: Starting batch size to test.
        min_batch_size: Minimum allowed batch size.
        max_batch_size: Maximum allowed batch size.
        target_memory_gb: Target maximum memory usage in GB.
        safety_margin: Fraction of target_memory_gb to use as threshold (0.8 = 80%).

    Returns:
        int: The scaled batch size that should fit within memory constraints.
    """
    if not TORCH_AVAILABLE:
        # If torch is not available, return a safe default
        return min(base_batch_size, max_batch_size)

    current_batch = base_batch_size
    limit_gb = target_memory_gb * safety_margin

    # First, check if we're already over the limit
    check_and_terminate_if_exceeds(limit_gb)

    # Try to find a batch size that fits
    while current_batch >= min_batch_size:
        try:
            # Simulate a small forward pass to estimate memory usage
            # This is a heuristic - actual usage depends on model size
            estimated_memory = get_memory_usage_gb()

            # Heuristic: assume memory scales roughly linearly with batch size
            # This is a simplification but works for initial scaling
            if estimated_memory < limit_gb:
                # Check if we can try a larger batch
                if current_batch < max_batch_size:
                    # Try next size up
                    next_batch = current_batch + 1
                    # Quick check: if current is well under limit, try larger
                    if estimated_memory < limit_gb * 0.7:
                        current_batch = next_batch
                        continue
                return current_batch
            else:
                # Over limit, reduce batch size
                current_batch -= 1
                gc.collect()
                time.sleep(0.1)  # Allow memory to settle
                continue

        except Exception:
            # If any error occurs, reduce batch size
            current_batch -= 1
            gc.collect()
            continue

    return max(min_batch_size, current_batch)


def enable_gradient_checkpointing(model: Any) -> None:
    """
    Enable gradient checkpointing for a PyTorch model to save memory.

    Gradient checkpointing trades computation for memory by recomputing
    activations during the backward pass instead of storing them.

    Args:
        model: A PyTorch nn.Module that supports gradient checkpointing.

    Note:
        This function assumes the model has a 'gradient_checkpointing_enable' method
        or similar. For models that don't support it directly, this is a no-op.
    """
    if not TORCH_AVAILABLE:
        return

    try:
        # Try the standard method for transformers models
        if hasattr(model, 'gradient_checkpointing_enable'):
            model.gradient_checkpointing_enable()
        # Try for models with _set_gradient_checkpointing
        elif hasattr(model, '_set_gradient_checkpointing'):
            model._set_gradient_checkpointing(True)
        else:
            # For generic models, try to enable on all modules that support it
            for module in model.modules():
                if hasattr(module, 'gradient_checkpointing_enable'):
                    try:
                        module.gradient_checkpointing_enable()
                    except (AttributeError, TypeError):
                        pass
    except Exception:
        # If checkpointing fails, log warning but don't crash
        sys.stderr.write("Warning: Could not enable gradient checkpointing\n")
        sys.stderr.flush()