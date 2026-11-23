import psutil
import sys
import os
from typing import Optional

from utils.config import MAX_MEMORY_GB, MAX_CPU_CORES

class ResourceLimitExceeded(Exception):
    """Exception raised when resource limits are exceeded."""
    pass

# Thresholds (defaults from config, but can be overridden for testing)
CPU_LIMIT = float(MAX_CPU_CORES)
RAM_LIMIT_GB = float(MAX_MEMORY_GB)
RAM_LIMIT_BYTES = RAM_LIMIT_GB * (1024 ** 3)

# Check interval in seconds
CHECK_INTERVAL = 0.5

_watchdog_active = False
_watchdog_thread: Optional[threading.Thread] = None
_process = psutil.Process(os.getpid())


class ResourceLimitExceeded(Exception):
    """
    Exception raised when resource limits (CPU or RAM) are exceeded.
    This allows the calling wrapper to catch the specific condition
    and fail the task without falling back to alternative methods.
    """
    pass


def _check_resources() -> bool:
    """
    Check current RAM usage in GB.
    Returns the percentage of RAM used.
    """
    # CPU Usage: psutil.cpu_percent() returns percentage (0-100)
    # We need to compare against CPU_LIMIT (number of cores).
    # If CPU_LIMIT is 2, that means 200% usage is the threshold on a multi-core system.
    # psutil.cpu_percent() returns total system usage. To map to "cores", we divide by 100.
    # But wait: if limit is 2 cores on a 4-core machine, we want to kill if usage > 200%.
    # If limit is 2 cores on a 2-core machine, we kill if usage > 100%.
    # The config says MAX_CPU_CORES=2. This is an absolute cap on logical cores used.
    # So if CPU usage % > (CPU_LIMIT * 100), we kill.
    
    if current_ram > MAX_MEMORY_GB:
        raise ResourceLimitExceeded(
            f"RAM usage {current_ram:.2f}GB exceeds limit of {MAX_MEMORY_GB}GB"
        )
    
    if current_cpu > MAX_CPU_CORES * 100:
        raise ResourceLimitExceeded(
            f"CPU usage {current_cpu:.1f}% exceeds limit of {MAX_CPU_CORES * 100}%"
        )

def monitor_resources(interval: float = 1.0, callback: Optional[callable] = None) -> None:
    """
    Background thread loop that checks resources periodically.
    Raises ResourceLimitExceeded if limits are breached.
    """
    global _watchdog_active
    logger.info(f"ResourceWatchdog started. Limits: CPU={CPU_LIMIT} cores, RAM={RAM_LIMIT_GB} GB")

    while _watchdog_active:
        if _check_resources():
            logger.critical("Resource limits exceeded. Raising ResourceLimitExceeded.")
            raise ResourceLimitExceeded(
                f"Resource limit exceeded: CPU {psutil.cpu_percent(interval=None):.1f}% "
                f"or RAM {_process.memory_info().rss / (1024**3):.2f} GB"
            )
        
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
    If limits are exceeded during execution, raises ResourceLimitExceeded.
    The caller MUST catch this exception and exit with code 1.

    Args:
        func: The function to execute.
        *args: Arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
    """
    start_watchdog()
    try:
        func(*args, **kwargs)
    except ResourceLimitExceeded:
        # Re-raise to allow the wrapper to handle the exit code
        raise
    finally:
        stop_watchdog()


# Convenience function to manually check resources (for non-threaded contexts)
def check_and_raise_if_needed() -> bool:
    """
    Perform a single resource check. If limits are exceeded, raises ResourceLimitExceeded.
    Returns False if resources are within limits.
    """
    if _check_resources():
        raise ResourceLimitExceeded(
            f"Resource limit exceeded: CPU {psutil.cpu_percent(interval=None):.1f}% "
            f"or RAM {_process.memory_info().rss / (1024**3):.2f} GB"
        )
    return False
