import os
import sys
import gc
import time
import psutil
from typing import Optional, Callable, Any
import torch
import torch.nn as nn

def get_memory_usage_gb() -> float:
    """
    Returns the current RAM usage of the current process in GB.
    Uses psutil for cross-platform accuracy.
    """
    process = psutil.Process(os.getpid())
    # rss (Resident Set Size) is the portion of memory occupied by a process
    # that resides in main memory (RAM).
    mem_bytes = process.memory_info().rss
    return mem_bytes / (1024 ** 3)

def check_and_terminate_if_exceeds(limit_gb: float) -> None:
    """
    Hard RAM watchdog: checks current process memory usage.
    If usage exceeds limit_gb, it forces garbage collection and checks again.
    If still exceeding, it terminates the process immediately with exit code 1.
    
    This is a 'fail loudly' mechanism to prevent OOM crashes that corrupt
    the execution environment or produce silent failures.
    
    Args:
        limit_gb: Maximum allowed RAM usage in Gigabytes.
    
    Raises:
        SystemExit: If memory usage exceeds the limit after GC.
    """
    current_usage = get_memory_usage_gb()
    
    if current_usage > limit_gb:
        # Attempt aggressive garbage collection before final check
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Re-check after GC
        current_usage = get_memory_usage_gb()
        
        if current_usage > limit_gb:
            print(f"CRITICAL: RAM usage ({current_usage:.2f} GB) exceeds limit ({limit_gb:.2f} GB). Terminating process.", file=sys.stderr)
            # Use os._exit to immediately terminate the process, bypassing cleanup
            # which might fail if memory is critically low.
            os._exit(1)

def enable_gradient_checkpointing(model: nn.Module) -> None:
    """
    Enables gradient checkpointing for a PyTorch model to save memory during backpropagation.
    This trades compute for memory by recomputing activations instead of storing them.
    
    Note: This assumes the model has a 'gradient_checkpointing_enable' method (common in HuggingFace models).
    If the method doesn't exist, it attempts to find 'use_gradient_checkpointing' attribute.
    
    Args:
        model: The PyTorch model to modify.
    """
    if hasattr(model, 'gradient_checkpointing_enable'):
        model.gradient_checkpointing_enable()
        print("Gradient checkpointing enabled via gradient_checkpointing_enable().")
    elif hasattr(model, 'use_gradient_checkpointing'):
        model.use_gradient_checkpointing = True
        print("Gradient checkpointing enabled via use_gradient_checkpointing attribute.")
    else:
        # Try to apply it recursively to children if it's a container
        for name, child in model.named_children():
            if hasattr(child, 'gradient_checkpointing_enable'):
                child.gradient_checkpointing_enable()
            elif hasattr(child, 'use_gradient_checkpointing'):
                child.use_gradient_checkpointing = True
            else:
                # Fallback: try to set a generic attribute if the model supports it
                try:
                    setattr(child, 'gradient_checkpointing', True)
                except AttributeError:
                    pass
        print("Attempted to enable gradient checkpointing on submodules.")

def auto_scale_batch_size(
    get_batch_fn: Callable[[int], Any],
    train_step_fn: Callable[[Any], float],
    initial_batch_size: int = 4,
    max_batch_size: int = 32,
    min_batch_size: int = 1,
    memory_limit_gb: float = 6.0,
    factor: int = 2
) -> int:
    """
    Auto-scales batch size from initial up to max, or down to min, based on memory constraints.
    
    This function attempts to find the largest batch size that fits within the memory limit.
    It starts at initial_batch_size, tries to run a step, checks memory. If memory is safe,
    it doubles the batch size and tries again. If memory exceeds limit, it halves the batch size
    (or goes to min) and stops increasing.
    
    Args:
        get_batch_fn: Function that takes batch_size and returns a batch.
        train_step_fn: Function that takes a batch and returns loss (triggers forward/backward).
        initial_batch_size: Starting batch size.
        max_batch_size: Upper bound for batch size.
        min_batch_size: Lower bound for batch size.
        memory_limit_gb: RAM limit in GB (passed to check_and_terminate_if_exceeds).
        factor: Multiplier to increase batch size (default 2).
    
    Returns:
        The optimal batch size found that fits within memory constraints.
    """
    current_bs = initial_batch_size
    best_bs = min_batch_size
    
    print(f"Starting batch size auto-scaling with initial={initial_batch_size}, limit={memory_limit_gb}GB")
    
    while current_bs <= max_batch_size:
        try:
            # Clear cache before test
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Get batch
            batch = get_batch_fn(current_bs)
            
            # Run step (this is where memory spikes)
            # We wrap in try/except to catch OOM if the watchdog doesn't kill fast enough
            train_step_fn(batch)
            
            # Check memory usage after the step
            usage = get_memory_usage_gb()
            if usage > memory_limit_gb:
                print(f"Memory usage ({usage:.2f} GB) exceeded limit at batch_size={current_bs}. Scaling down.")
                current_bs = max(current_bs // factor, min_batch_size)
                break
            
            # If successful and under limit, this is a candidate
            best_bs = current_bs
            print(f"Batch size {current_bs} fits (usage: {usage:.2f} GB). Trying larger...")
            
            # Try to scale up
            next_bs = current_bs * factor
            if next_bs > max_batch_size:
                break
            current_bs = next_bs
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                print(f"OOM error at batch_size={current_bs}. Scaling down.")
                current_bs = max(current_bs // factor, min_batch_size)
                # If we are already at min, we can't go lower
                if current_bs == min_batch_size:
                    print(f"Cannot fit even minimum batch size {min_batch_size}.")
                    break
            else:
                raise e
    
    print(f"Selected optimal batch size: {best_bs}")
    return best_bs