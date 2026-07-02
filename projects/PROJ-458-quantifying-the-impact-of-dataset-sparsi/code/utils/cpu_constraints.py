"""CPU and memory constraint utilities.

This module provides utilities for enforcing memory limits and iterating
over large datasets in chunks to prevent Out-of-Memory (OOM) errors.
"""
import gc
import os
import resource
import sys
from typing import Any, Callable, Iterator, List, Optional, TypeVar

import psutil

from utils.logging import get_logger

logger = get_logger("cpu_constraints")

def get_current_memory_mb() -> float:
    """Get current memory usage of the process in MB.

    Returns:
        Current RSS (Resident Set Size) memory usage in megabytes.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)

def enforce_memory_limit(limit_mb: float, check_interval: int = 1000) -> bool:
    """
    Enforce a memory limit by checking current usage, triggering garbage collection,
    and optionally setting a hard resource limit on Unix-like systems.

    This function performs the following steps:
    1. Checks current memory usage.
    2. If limit is exceeded, triggers garbage collection.
    3. Checks again. If still exceeded, logs a critical error and returns False.
    4. On Unix systems, attempts to set a hard resource limit (RLIMIT_AS) if not already set
       or if the current limit is higher than the requested limit, to prevent future OOMs.

    Args:
        limit_mb: Maximum allowed memory in MB.
        check_interval: Placeholder for operation counting logic (currently unused but preserved for API compatibility).

    Returns:
        True if memory is within limit (or could be managed), False if limit is strictly exceeded.
    """
    current_mem = get_current_memory_mb()

    if current_mem > limit_mb:
        logger.warning(
            f"Memory limit exceeded: {current_mem:.2f}MB > {limit_mb}MB. Triggering GC."
        )
        gc.collect()
        # Force a second check immediately after GC
        current_mem = get_current_memory_mb()
        if current_mem > limit_mb:
            logger.error(
                f"Critical: Memory still exceeds limit after GC: {current_mem:.2f}MB"
            )
            return False

    # Attempt to set a hard resource limit on Unix-like systems to enforce the limit
    # at the OS level for subsequent allocations.
    if os.name != "nt":  # Skip on Windows as resource module is limited
        try:
            # Get current soft/hard limits
            soft, hard = resource.getrlimit(resource.RLIMIT_AS)
            limit_bytes = int(limit_mb * 1024 * 1024)

            # Only set if the requested limit is stricter than the current hard limit
            # or if the current hard limit is unlimited (-1)
            if hard == -1 or limit_bytes < hard:
                # Set soft limit to the limit, hard limit slightly higher to allow some overhead
                # or exactly the limit if strict enforcement is needed.
                # We use the limit for both to be strict.
                resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
                logger.debug(f"Set RLIMIT_AS to {limit_mb}MB")
        except ValueError as e:
            # Limit might be too low or not allowed by user permissions
            logger.warning(f"Could not set resource limit: {e}")
        except Exception as e:
            logger.warning(f"Error managing resource limits: {e}")

    return True

T = TypeVar("T")

def chunked_iterator(
    iterable: List[T],
    chunk_size: int = 1000,
    memory_limit_mb: float = 4096.0,
) -> Iterator[List[T]]:
    """
    Yield successive chunks from a list, checking memory constraints before each yield.

    This generator is designed to process large lists without loading the entire
    dataset into memory at once, while also monitoring current RSS to prevent OOM.

    Args:
        iterable: List of items to iterate over.
        chunk_size: Number of items per chunk.
        memory_limit_mb: Memory limit in MB. If exceeded, the iteration stops.

    Yields:
        Lists of items (chunks) from the original iterable.
    """
    total_items = len(iterable)
    logger.info(f"Starting chunked iteration over {total_items} items with limit {memory_limit_mb}MB")

    for i in range(0, total_items, chunk_size):
        # Check memory before yielding a new chunk
        if not enforce_memory_limit(memory_limit_mb):
            logger.error(
                f"Memory limit reached at chunk {i // chunk_size}. Stopping iteration."
            )
            break

        # Extract the chunk
        chunk = iterable[i : i + chunk_size]

        # Yield the chunk
        yield chunk

        # Explicitly delete the chunk reference to hint GC, though the caller usually holds it
        # We check memory again to decide if we should force GC before the next iteration
        current_mem = get_current_memory_mb()
        if current_mem > (memory_limit_mb * 0.9):
            logger.debug(f"Memory high ({current_mem:.2f}MB) after chunk. Triggering GC.")
            gc.collect()