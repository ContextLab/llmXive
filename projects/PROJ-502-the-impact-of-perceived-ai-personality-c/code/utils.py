"""
Utility functions for the AI Personality Consistency research pipeline.

This module provides:
- Dynamic batch size calculation to ensure RAM usage stays under a configurable limit.
- Memory monitoring utilities for batch processing loops.
- Logging helpers.
"""

import gc
import os
import sys
import traceback
from typing import List, Optional, Tuple, Dict, Any, Callable

import psutil

# Import from sibling module (T004)
from config import get_config, get_model_config

# Constants
DEFAULT_MAX_RAM_GB = 7.0
DEFAULT_BATCH_SIZE = 32
MB_PER_GB = 1024 * 1024 * 1024


def get_available_ram_gb() -> float:
    """
    Estimate the available RAM on the current system in GB.

    Returns:
        float: Available RAM in GB.
    """
    try:
        mem_info = psutil.virtual_memory()
        available_bytes = mem_info.available
        return available_bytes / MB_PER_GB
    except Exception:
        # Fallback to total memory if 'available' is not supported on some OS
        try:
            mem_info = psutil.virtual_memory()
            return mem_info.total / MB_PER_GB
        except Exception:
            # Hardcoded fallback if psutil fails completely
            return 4.0


def calculate_dynamic_batch_size(
    max_ram_gb: Optional[float] = None,
    estimated_memory_per_item_mb: float = 50.0,
    min_batch: int = 1,
    max_batch: int = 128
) -> int:
    """
    Calculate a dynamic batch size that ensures total RAM usage remains
    below a specified threshold (default <7GB).

    Args:
        max_ram_gb (float): Maximum RAM (in GB) allowed for the batch process.
                            Defaults to config value or 7.0.
        estimated_memory_per_item_mb (float): Estimated memory (in MB) consumed
                                              by a single data item during processing.
        min_batch (int): Minimum allowed batch size.
        max_batch (int): Maximum allowed batch size.

    Returns:
        int: The calculated batch size.
    """
    if max_ram_gb is None:
        cfg = get_config()
        max_ram_gb = float(cfg.get("max_ram_gb", DEFAULT_MAX_RAM_GB))

    # Convert max RAM to MB
    max_ram_mb = max_ram_gb * MB_PER_GB

    # Safety factor: use only 70% of allowed RAM for the batch to leave room for overhead
    safe_limit_mb = max_ram_mb * 0.70

    # Calculate batch size
    if estimated_memory_per_item_mb <= 0:
        estimated_memory_per_item_mb = 50.0  # Default fallback

    calculated = int(safe_limit_mb / estimated_memory_per_item_mb)

    # Clamp to min/max
    calculated = max(min_batch, min(calculated, max_batch))

    return calculated


def estimate_memory_per_item(model_name: str = "distilbert-base-uncased") -> float:
    """
    Estimate memory usage per item based on model size.

    Args:
        model_name (str): The name of the transformer model.

    Returns:
        float: Estimated memory in MB per item.
    """
    # Heuristic based on model size (simplified)
    # DistilBERT ~ 66M params -> ~264MB for weights (float32)
    # Activation memory varies, but let's estimate ~50-100MB per batch item for small models
    # For larger models, this scales up.
    if "distilbert" in model_name.lower():
        return 60.0
    elif "bert" in model_name.lower():
        return 100.0
    elif "roberta" in model_name.lower():
        return 120.0
    else:
        return 80.0


def get_memory_usage_mb() -> float:
    """
    Get current memory usage of the Python process in MB.

    Returns:
        float: Memory usage in MB.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)


class MemoryMonitor:
    """
    Context manager and utility for monitoring memory usage during batch processing.
    """

    def __init__(self, max_ram_gb: float = DEFAULT_MAX_RAM_GB, log_func: Optional[Callable] = None):
        """
        Args:
            max_ram_gb (float): Maximum allowed RAM in GB.
            log_func (callable): Optional logging function.
        """
        self.max_ram_gb = max_ram_gb
        self.max_ram_mb = max_ram_gb * MB_PER_GB
        self.log_func = log_func or print
        self.start_mem_mb = 0.0
        self.peak_mem_mb = 0.0

    def start(self):
        """Start monitoring."""
        self.start_mem_mb = get_memory_usage_mb()
        self.peak_mem_mb = self.start_mem_mb
        self.log_func(f"[MemoryMonitor] Started. Current: {self.start_mem_mb:.1f} MB")

    def check(self, current_item_index: int = -1) -> bool:
        """
        Check if current memory usage exceeds the limit.

        Args:
            current_item_index (int): Current item index (optional, for logging).

        Returns:
            bool: True if within limits, False if exceeded.
        """
        current_mem = get_memory_usage_mb()
        if current_mem > self.peak_mem_mb:
            self.peak_mem_mb = current_mem

        is_ok = current_mem < self.max_ram_mb

        if not is_ok:
            self.log_func(
                f"[MemoryMonitor] WARNING: Memory limit exceeded! "
                f"Current: {current_mem:.1f} MB, Limit: {self.max_ram_mb:.1f} MB. "
                f"Item index: {current_item_index}"
            )
            # Force garbage collection
            gc.collect()
        else:
            # Optional: log progress periodically
            if current_item_index > 0 and current_item_index % 100 == 0:
                self.log_func(f"[MemoryMonitor] Progress: {current_item_index}. Current: {current_mem:.1f} MB, Peak: {self.peak_mem_mb:.1f} MB")

        return is_ok

    def get_peak_mb(self) -> float:
        """Return peak memory usage in MB."""
        return self.peak_mem_mb

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.log_func(
            f"[MemoryMonitor] Finished. Peak: {self.peak_mem_mb:.1f} MB. "
            f"Start: {self.start_mem_mb:.1f} MB. Diff: {self.peak_mem_mb - self.start_mem_mb:.1f} MB"
        )
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_val, exc_tb)
        return False


def create_batch_iterator(
    data: List[Any],
    batch_size: int,
    monitor: Optional[MemoryMonitor] = None
) -> List[List[Any]]:
    """
    Create batches from a list, optionally monitoring memory.

    Args:
        data (List[Any]): The full dataset.
        batch_size (int): Size of each batch.
        monitor (MemoryMonitor): Optional memory monitor instance.

    Returns:
        List[List[Any]]: List of batches.
    """
    batches = []
    for i in range(0, len(data), batch_size):
        batch = data[i : i + batch_size]
        if monitor:
            if not monitor.check(i):
                # If memory is exceeded, we might want to stop or reduce batch size
                # For now, we just log and continue, but in a real scenario,
                # one might break or dynamically adjust.
                pass
        batches.append(batch)
    return batches

# Export public names
__all__ = [
    "calculate_dynamic_batch_size",
    "estimate_memory_per_item",
    "get_available_ram_gb",
    "get_memory_usage_mb",
    "MemoryMonitor",
    "create_batch_iterator",
    "DEFAULT_MAX_RAM_GB",
    "DEFAULT_BATCH_SIZE",
]