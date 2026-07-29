"""
Resource Monitor Module for llmXive.

Implements a background thread to monitor RAM usage and trigger early exit
if memory usage exceeds the safety threshold (6.5 GB).
"""
import os
import sys
import time
import threading
import logging
import resource
from typing import Optional, Callable, List

# Constants
MEMORY_THRESHOLD_GB = 6.5
MEMORY_THRESHOLD_BYTES = MEMORY_THRESHOLD_GB * 1024 * 1024 * 1024
POLL_INTERVAL_SECONDS = 2.0
LOG_INTERVAL_SECONDS = 10.0

# Global state
_monitor_thread: Optional[threading.Thread] = None
_stop_event: threading.Event = threading.Event()
_logger: Optional[logging.Logger] = None
_last_log_time: float = 0.0
_max_observed_memory_bytes: float = 0.0
_memory_history: List[float] = []

def _get_memory_usage_bytes() -> float:
    """
    Get current memory usage in bytes.
    Uses resource module for cross-platform compatibility (primarily Unix).
    Falls back to psutil if available, otherwise estimates via resource.
    """
    try:
        # Try psutil first if available (more accurate on some systems)
        import psutil
        process = psutil.Process(os.getpid())
        return float(process.memory_info().rss)
    except ImportError:
        # Fallback to resource module (Unix/Linux/macOS)
        # Note: resource.getrusage returns maxrss in kilobytes on Unix
        usage = resource.getrusage(resource.RUSAGE_SELF)
        maxrss_kb = usage.ru_maxrss
        # On macOS, ru_maxrss is in bytes; on Linux it's in KB.
        # We'll assume Linux behavior (KB) and add a check for macOS.
        if sys.platform == 'darwin':
            # macOS: ru_maxrss is in bytes
            return float(maxrss_kb)
        else:
            # Linux/Unix: ru_maxrss is in KB
            return float(maxrss_kb * 1024)

def _monitor_loop(
    threshold_bytes: float,
    on_threshold_exceeded: Optional[Callable[[], None]] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Background loop that monitors memory usage.
    Logs usage periodically and triggers exit if threshold is exceeded.
    """
    global _max_observed_memory_bytes, _last_log_time, _memory_history

    if logger is None:
        logger = logging.getLogger(__name__)

    _logger = logger
    _last_log_time = time.time()

    logger.info(
        f"ResourceMonitor started: threshold={threshold_bytes / (1024**3):.2f} GB, "
        f"interval={POLL_INTERVAL_SECONDS}s"
    )

    while not _stop_event.is_set():
        try:
            current_mem = _get_memory_usage_bytes()
            _max_observed_memory_bytes = max(_max_observed_memory_bytes, current_mem)
            _memory_history.append(current_mem)

            # Log periodically
            now = time.time()
            if now - _last_log_time >= LOG_INTERVAL_SECONDS:
                logger.info(
                    f"RAM Usage: {current_mem / (1024**3):.3f} GB "
                    f"(Max: {_max_observed_memory_bytes / (1024**3):.3f} GB)"
                )
                _last_log_time = now

            # Check threshold
            if current_mem > threshold_bytes:
                logger.error(
                    f"CRITICAL: Memory usage ({current_mem / (1024**3):.3f} GB) "
                    f"exceeded threshold ({threshold_bytes / (1024**3):.3f} GB). "
                    f"Initiating early exit to prevent OOM."
                )
                if on_threshold_exceeded:
                    on_threshold_exceeded()
                else:
                    # Default behavior: log and exit
                    logger.error("Exiting process due to memory threshold exceeded.")
                    sys.exit(1)

        except Exception as e:
            logger.warning(f"ResourceMonitor error during check: {e}")

        _stop_event.wait(POLL_INTERVAL_SECONDS)

    logger.info("ResourceMonitor stopped.")

def start_monitor(
    threshold_gb: float = MEMORY_THRESHOLD_GB,
    on_threshold_exceeded: Optional[Callable[[], None]] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Start the resource monitoring background thread.

    Args:
        threshold_gb: Memory threshold in GB (default 6.5 GB).
        on_threshold_exceeded: Optional callback to run when threshold is exceeded.
        logger: Optional logger instance.
    """
    global _monitor_thread, _stop_event

    if _monitor_thread is not None and _monitor_thread.is_alive():
        logger = logger or logging.getLogger(__name__)
        logger.warning("ResourceMonitor is already running.")
        return

    _stop_event = threading.Event()
    threshold_bytes = threshold_gb * 1024 * 1024 * 1024

    _monitor_thread = threading.Thread(
        target=_monitor_loop,
        args=(threshold_bytes, on_threshold_exceeded, logger),
        daemon=True,
        name="ResourceMonitor"
    )
    _monitor_thread.start()

    logger = logger or logging.getLogger(__name__)
    logger.info(f"Started ResourceMonitor with threshold {threshold_gb} GB")

def stop_monitor() -> None:
    """Stop the resource monitoring thread."""
    global _monitor_thread

    if _monitor_thread is None or not _monitor_thread.is_alive():
        return

    _stop_event.set()
    _monitor_thread.join(timeout=5.0)

    if _monitor_thread.is_alive():
        logging.getLogger(__name__).warning("ResourceMonitor did not stop gracefully.")

    _monitor_thread = None

def get_max_memory_usage_gb() -> float:
    """
    Get the maximum memory usage observed by the monitor in GB.

    Returns:
        float: Max memory in GB, or 0.0 if monitor hasn't run.
    """
    return _max_observed_memory_bytes / (1024 * 1024 * 1024)

def get_memory_history() -> List[float]:
    """
    Get the history of memory observations in bytes.

    Returns:
        List[float]: List of memory usage values in bytes.
    """
    return list(_memory_history)

def log_current_memory_usage(logger: Optional[logging.Logger] = None) -> None:
    """
    Log the current memory usage immediately.
    """
    current = _get_memory_usage_bytes()
    logger = logger or logging.getLogger(__name__)
    logger.info(f"Current RAM Usage: {current / (1024**3):.3f} GB")

# Context manager for scoped monitoring
class MemoryGuard:
    """
    Context manager to monitor memory usage within a specific block of code.
    Exits if threshold is exceeded.
    """

    def __init__(
        self,
        threshold_gb: float = MEMORY_THRESHOLD_GB,
        logger: Optional[logging.Logger] = None
    ):
        self.threshold_gb = threshold_gb
        self.logger = logger or logging.getLogger(__name__)
        self.start_mem = 0.0
        self.end_mem = 0.0

    def __enter__(self):
        self.start_mem = _get_memory_usage_bytes()
        self.logger.info(f"MemoryGuard entered. Start: {self.start_mem / (1024**3):.3f} GB")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_mem = _get_memory_usage_bytes()
        delta = self.end_mem - self.start_mem
        self.logger.info(
            f"MemoryGuard exited. End: {self.end_mem / (1024**3):.3f} GB, "
            f"Delta: {delta / (1024**3):.3f} GB"
        )
        if self.end_mem > self.threshold_gb * 1024 * 1024 * 1024:
            self.logger.error(
                f"MemoryGuard threshold exceeded inside context: "
                f"{self.end_mem / (1024**3):.3f} GB > {self.threshold_gb} GB"
            )
            # Do not suppress exception, but log the issue
            # The caller or the global monitor should handle the exit
        return False

def main() -> None:
    """
    Standalone runner for testing the resource monitor.
    Simulates memory usage to verify threshold detection.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info("Starting ResourceMonitor test...")
    start_monitor(threshold_gb=0.5, logger=logger)  # Use 0.5GB for quick test

    # Simulate some work
    data = []
    for i in range(100):
        time.sleep(0.1)
        # Allocate memory to trigger threshold
        data.append([0] * 1000000)
        if i % 10 == 0:
            log_current_memory_usage(logger)

    # Wait a bit to see logs
    time.sleep(5)

    stop_monitor()
    logger.info(f"Max memory observed: {get_max_memory_usage_gb():.3f} GB")

if __name__ == "__main__":
    main()
