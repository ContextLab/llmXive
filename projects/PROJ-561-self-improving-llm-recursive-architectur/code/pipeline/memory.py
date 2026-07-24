"""
Memory management utilities for dynamic batch size reduction and RAM enforcement.

Implements SC-005: Explicitly verify GB limit is respected; if not, terminate.
"""
import os
import sys
import gc
import time
import psutil
from typing import Optional, Callable, Any, Tuple
import torch
import logging

# Configuration constants
RAM_LIMIT_GB = 6.5
MIN_BATCH_SIZE = 1

def get_memory_usage_gb() -> float:
    """
    Get current RAM usage in Gigabytes.
    
    Returns:
        float: Current RAM usage in GB.
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return memory_info.rss / (1024 ** 3)

def check_and_terminate_if_exceeds(limit_gb: float = RAM_LIMIT_GB) -> None:
    """
    Check if RAM usage exceeds limit and terminate process if it does.
    
    Args:
        limit_gb: RAM limit in GB. Defaults to 6.5GB.
        
    Raises:
        SystemExit: If RAM usage exceeds the limit.
    """
    current_usage = get_memory_usage_gb()
    if current_usage > limit_gb:
        logging.critical(f"RAM usage {current_usage:.2f}GB exceeds limit {limit_gb}GB. Terminating.")
        sys.exit(1)

def enable_gradient_checkpointing(model: torch.nn.Module) -> None:
    """
    Enable gradient checkpointing for a model to reduce memory usage.
    
    Args:
        model: PyTorch model to enable checkpointing on.
    """
    if hasattr(model, 'gradient_checkpointing_enable'):
        model.gradient_checkpointing_enable()
        logging.info("Gradient checkpointing enabled.")
    else:
        logging.warning("Model does not support gradient checkpointing.")

def auto_scale_batch_size(
    batch_size: int,
    current_ram_gb: float,
    limit_gb: float = RAM_LIMIT_GB
) -> Tuple[int, bool]:
    """
    Automatically scale down batch size if RAM usage is too high.
    
    Args:
        batch_size: Current batch size.
        current_ram_gb: Current RAM usage in GB.
        limit_gb: RAM limit in GB.
        
    Returns:
        Tuple of (new_batch_size, should_terminate)
    """
    if current_ram_gb <= limit_gb:
        return batch_size, False
    
    new_batch_size = batch_size // 2
    
    if new_batch_size < MIN_BATCH_SIZE:
        logging.error("OOM: Batch size would be reduced below minimum. Terminating.")
        return 0, True
    
    logging.warning(
        f"RAM usage {current_ram_gb:.2f}GB exceeds limit {limit_gb}GB. "
        f"Reducing batch size from {batch_size} to {new_batch_size}."
    )
    return new_batch_size, False

def run_epoch_with_memory_monitoring(
    train_epoch_func: Callable,
    model: torch.nn.Module,
    dataloader: Any,
    optimizer: torch.optim.Optimizer,
    initial_batch_size: int,
    limit_gb: float = RAM_LIMIT_GB
) -> bool:
    """
    Run a training epoch with dynamic batch size reduction and memory monitoring.
    
    Args:
        train_epoch_func: Function that performs the actual training epoch.
                        Signature: train_epoch_func(model, dataloader, optimizer, batch_size)
        model: PyTorch model to train.
        dataloader: DataLoader for training data.
        optimizer: Optimizer for the model.
        initial_batch_size: Starting batch size.
        limit_gb: RAM limit in GB.
        
    Returns:
        bool: True if epoch completed successfully, False if OOM occurred.
    """
    batch_size = initial_batch_size
    max_retries = 3  # Prevent infinite loops
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Check memory before starting
            current_ram = get_memory_usage_gb()
            check_and_terminate_if_exceeds(limit_gb)
            
            # Adjust dataloader batch size
            dataloader.batch_size = batch_size
            if hasattr(dataloader, 'batch_sampler'):
                dataloader.batch_sampler.batch_size = batch_size
            
            logging.info(f"Starting epoch with batch size {batch_size}")
            
            # Run the training epoch
            train_epoch_func(model, dataloader, optimizer, batch_size)
            
            # Check memory after epoch
            current_ram = get_memory_usage_gb()
            if current_ram > limit_gb:
                logging.warning(f"Post-epoch RAM {current_ram:.2f}GB exceeds limit. Reducing batch size.")
                batch_size, should_terminate = auto_scale_batch_size(batch_size, current_ram, limit_gb)
                if should_terminate:
                    return False
                retry_count += 1
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                continue
            
            logging.info(f"Epoch completed successfully with batch size {batch_size}")
            return True
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower() or "OOM" in str(e):
                logging.warning(f"OOM detected: {e}. Attempting batch size reduction.")
                batch_size, should_terminate = auto_scale_batch_size(batch_size, get_memory_usage_gb(), limit_gb)
                if should_terminate:
                    return False
                retry_count += 1
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                continue
            else:
                raise
    
    logging.error("Max retries exceeded for batch size reduction. Terminating.")
    return False

class MemoryWatchdog:
    """
    Context manager for monitoring memory during training operations.
    """
    
    def __init__(self, limit_gb: float = RAM_LIMIT_GB, check_interval: float = 1.0):
        self.limit_gb = limit_gb
        self.check_interval = check_interval
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        final_ram = get_memory_usage_gb()
        logging.info(f"Memory watchdog: Elapsed {elapsed:.2f}s, Final RAM {final_ram:.2f}GB")
        return False
        
    def check(self) -> bool:
        """
        Check current memory usage and terminate if exceeded.
        
        Returns:
            bool: True if within limits, False if exceeded.
        """
        current_ram = get_memory_usage_gb()
        if current_ram > self.limit_gb:
            logging.critical(f"Memory watchdog triggered: {current_ram:.2f}GB > {self.limit_gb}GB")
            sys.exit(1)
        return True

def enforce_ram_limit(limit_gb: float = RAM_LIMIT_GB) -> None:
    """
    Enforce RAM limit by checking current usage and terminating if exceeded.
    
    Args:
        limit_gb: RAM limit in GB. Defaults to 6.5GB.
    """
    current_ram = get_memory_usage_gb()
    if current_ram > limit_gb:
        logging.critical(f"RAM limit exceeded: {current_ram:.2f}GB > {limit_gb}GB. Terminating.")
        sys.exit(1)
    logging.debug(f"RAM check passed: {current_ram:.2f}GB <= {limit_gb}GB")