"""
Resource Watchdog for llmXive pipeline.

Actively monitors CPU and RAM usage at runtime. If limits are exceeded
(2 cores, 7GB RAM), the process is terminated immediately.

This module is designed to be imported and wrapped around execution tasks
to enforce the resource constraints defined in code/utils/config.py.
"""

import os
import signal
import sys
import threading
import time
from typing import Callable, Optional

import psutil

from .config import MAX_CPU_CORES, MAX_MEMORY_GB
from .logging import get_logger

logger = get_logger(__name__)

# Thresholds (defaults from config, but can be overridden for testing)
CPU_LIMIT = float(MAX_CPU_CORES)
RAM_LIMIT_GB = float(MAX_MEMORY_GB)
RAM_LIMIT_BYTES = RAM_LIMIT_GB * (1024 ** 3)

# Check interval in seconds
CHECK_INTERVAL = 0.5

_watchdog_active = False
_watchdog_thread: Optional[threading.Thread] = None
_process = psutil.Process(os.getpid())


def _check_resources() -> bool:
    """
    Check current CPU and RAM usage.

    Returns:
        True if limits are exceeded and action should be taken.
        False if resources are within limits.
    """
    # CPU Usage: psutil.cpu_percent() returns percentage (0-100)
    # We need to compare against CPU_LIMIT (number of cores).
    # If CPU_LIMIT is 2, that means 200% usage is the threshold on a multi-core system.
    # However, the constraint usually implies "do not use more than N cores worth of compute".
    # psutil.cpu_percent() returns total system usage. To map to "cores", we divide by 100.
    # But wait: if limit is 2 cores on a 4-core machine, we want to kill if usage > 200%.
    # If limit is 2 cores on a 2-core machine, we kill if usage > 100%.
    # The config says MAX_CPU_CORES=2. This is an absolute cap on logical cores used.
    # So if CPU usage % > (CPU_LIMIT * 100), we kill.
    
    current_cpu_percent = psutil.cpu_percent(interval=None)
    cpu_threshold_percent = CPU_LIMIT * 100.0

    if current_cpu_percent > cpu_threshold_percent:
        logger.warning(
            f"CPU usage ({current_cpu_percent:.1f}%) exceeded limit ({cpu_threshold_percent:.1f}%). "
            f"Limit corresponds to {CPU_LIMIT} cores."
        )
        return True

    # RAM Usage
    memory_info = _process.memory_info()
    current_ram_bytes = memory_info.rss
    
    if current_ram_bytes > RAM_LIMIT_BYTES:
        logger.warning(
            f"RAM usage ({current_ram_bytes / (1024**3):.2f} GB) exceeded limit ({RAM_LIMIT_GB} GB)."
        )
        return True

    return False


def _watchdog_loop() -> None:
    """
    Background thread loop that checks resources periodically.
    """
    global _watchdog_active
    logger.info(f"ResourceWatchdog started. Limits: CPU={CPU_LIMIT} cores, RAM={RAM_LIMIT_GB} GB")

    while _watchdog_active:
        if _check_resources():
            logger.critical("Resource limits exceeded. Terminating process immediately.")
            # Use SIGKILL to ensure immediate termination, bypassing cleanup handlers
            # to prevent hanging on resource-heavy cleanup if that's the cause.
            os.kill(os.getpid(), signal.SIGKILL)
            # Fallback exit in case signal handling is overridden
            sys.exit(1)
        
        time.sleep(CHECK_INTERVAL)


def start_watchdog(interval: float = CHECK_INTERVAL) -> None:
    """
    Start the resource watchdog in a background daemon thread.

    Args:
        interval: Time in seconds between resource checks.
    """
    global _watchdog_active, _watchdog_thread, CHECK_INTERVAL
    
    if _watchdog_active:
        logger.warning("ResourceWatchdog is already running.")
        return

    CHECK_INTERVAL = interval
    _watchdog_active = True
    _watchdog_thread = threading.Thread(target=_watchdog_loop, daemon=True)
    _watchdog_thread.start()
    logger.debug("ResourceWatchdog thread started.")


def stop_watchdog() -> None:
    """
    Stop the resource watchdog.
    """
    global _watchdog_active
    if not _watchdog_active:
        return
    
    _watchdog_active = False
    if _watchdog_thread and _watchdog_thread.is_alive():
        _watchdog_thread.join(timeout=1.0)
        if _watchdog_thread.is_alive():
            logger.warning("Failed to stop watchdog thread gracefully.")
    logger.info("ResourceWatchdog stopped.")


def run_with_watchdog(func: Callable, *args, **kwargs) -> None:
    """
    Run a function while actively monitoring resources.
    If limits are exceeded during execution, the process will be killed.

    Args:
        func: The function to execute.
        *args: Arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
    """
    start_watchdog()
    try:
        func(*args, **kwargs)
    finally:
        stop_watchdog()


# Convenience function to manually check resources (for non-threaded contexts)
def check_and_kill_if_needed() -> bool:
    """
    Perform a single resource check. If limits are exceeded, kill the process.
    Returns True if the process was killed (should not return normally in that case).
    Returns False if resources are within limits.
    """
    if _check_resources():
        logger.critical("Resource limits exceeded. Terminating process immediately.")
        os.kill(os.getpid(), signal.SIGKILL)
        sys.exit(1)
    return False