"""
Global memory monitoring module for the llmXive research pipeline.

This module implements aggregate RAM usage tracking across the main process
and all spawned child processes. It enforces a strict memory limit (default 7GB)
and raises MemoryLimitExceeded if the threshold is breached.

Dependencies:
    - psutil: Required for process and child process memory inspection.
"""

import os
import sys
import time
import logging
import threading
from typing import Optional, Callable
from pathlib import Path

import psutil

# Import shared exceptions from ingest to maintain consistency across the pipeline
# The API surface in code/src/ingest.py defines MemoryLimitExceeded
try:
    from src.ingest import MemoryLimitExceeded
except ImportError:
    # Fallback definition if imported standalone, though ingest should define it
    class MemoryLimitExceeded(Exception):
        """Raised when aggregate memory usage exceeds the configured limit."""
        pass


# Default limit: 7 GB in bytes
DEFAULT_MEMORY_LIMIT_BYTES = 7 * 1024 * 1024 * 1024

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_current_memory_usage_bytes() -> int:
    """
    Calculate the aggregate RSS (Resident Set Size) memory usage in bytes.

    This includes the main process and all its direct and indirect children.
    This function is used to enforce the global memory limit.

    Returns:
        int: Total memory usage in bytes.

    Raises:
        MemoryLimitExceeded: If the calculated aggregate memory exceeds the limit.
    """
    process = psutil.Process(os.getpid())
    
    # Get memory info for the main process
    try:
        main_mem = process.memory_info().rss
    except psutil.NoSuchProcess:
        logger.error("Main process not found during memory check.")
        main_mem = 0

    total_mem = main_mem

    # Sum memory of all child processes
    try:
        children = process.children(recursive=True)
        for child in children:
            try:
                # Use memory_info().rss for consistency with main process
                child_mem = child.memory_info().rss
                total_mem += child_mem
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Child process might have terminated or be inaccessible
                continue
    except psutil.NoSuchProcess:
        # Main process vanished (unlikely but possible in race conditions)
        pass

    return total_mem


def validate_ram_limit(memory_limit_bytes: Optional[int] = None) -> None:
    """
    Check current memory usage against a limit.

    Args:
        memory_limit_bytes: The maximum allowed memory in bytes. Defaults to 7GB.

    Raises:
        MemoryLimitExceeded: If usage exceeds the limit.
    """
    if memory_limit_bytes is None:
        memory_limit_bytes = DEFAULT_MEMORY_LIMIT_BYTES

    current_usage = get_current_memory_usage_bytes()
    
    logger.info(f"Current aggregate memory usage: {current_usage / (1024**3):.2f} GB "
                f"(Limit: {memory_limit_bytes / (1024**3):.2f} GB)")

    if current_usage > memory_limit_bytes:
        logger.error(f"Memory limit exceeded! Usage: {current_usage} bytes, "
                     f"Limit: {memory_limit_bytes} bytes")
        raise MemoryLimitExceeded(
            f"Aggregate memory usage ({current_usage} bytes) exceeds limit "
            f"({memory_limit_bytes} bytes)"
        )


def monitor_memory_periodically(
    interval_seconds: float = 5.0,
    memory_limit_bytes: Optional[int] = None,
    stop_event: Optional[threading.Event] = None
) -> None:
    """
    Run a background thread that periodically checks memory usage.

    This function starts a daemon thread that calls `validate_ram_limit` at
    regular intervals. If the limit is exceeded, it logs the error and raises
    `MemoryLimitExceeded`, which will propagate to the main thread if not caught.

    Args:
        interval_seconds: How often to check memory (seconds).
        memory_limit_bytes: The memory limit in bytes.
        stop_event: A threading.Event to signal the monitor to stop.
    """
    if memory_limit_bytes is None:
        memory_limit_bytes = DEFAULT_MEMORY_LIMIT_BYTES

    def _monitor_loop():
        while True:
            if stop_event and stop_event.is_set():
                logger.debug("Memory monitor stopped by event.")
                break
            
            try:
                validate_ram_limit(memory_limit_bytes)
            except MemoryLimitExceeded as e:
                logger.critical(str(e))
                # Re-raise to halt the pipeline as per requirement
                raise e
            
            # Sleep in small increments to allow responsive stopping
            time.sleep(interval_seconds)

    # Start the monitor in a daemon thread
    monitor_thread = threading.Thread(target=_monitor_loop, daemon=True)
    monitor_thread.start()
    logger.info(f"Memory monitor started (interval={interval_seconds}s, "
                f"limit={memory_limit_bytes / (1024**3):.2f} GB)")
    
    # Return the thread and event so the caller can manage them if needed
    return monitor_thread, stop_event or threading.Event()


def check_memory_at_checkpoint() -> None:
    """
    A convenience function to be called at major data load checkpoints.
    
    Performs a single, synchronous check of aggregate memory usage.
    """
    validate_ram_limit()


def main() -> None:
    """
    Entry point for testing the monitor module directly.
    
    This function runs a simple loop that checks memory usage every 2 seconds
    until interrupted or limit exceeded.
    """
    logger.info("Starting memory monitor test (Ctrl+C to stop)...")
    try:
        while True:
            check_memory_at_checkpoint()
            time.sleep(2)
    except KeyboardInterrupt:
        logger.info("Monitor interrupted by user.")
    except MemoryLimitExceeded as e:
        logger.error(f"Pipeline halted: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()