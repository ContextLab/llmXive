"""
Memory monitoring utilities for the pipeline.

This module provides memory monitoring capabilities to ensure
the pipeline stays within the 7GB memory limit (SC-002).
"""
import logging
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from config import get_memory_limit_mb

# Global monitoring state
_monitor_thread: Optional[threading.Thread] = None
_monitor_stop_event: Optional[threading.Event] = None
_monitor_log_file: Optional[Path] = None
_monitor_interval_seconds = 1.0
_peak_memory_mb = 0.0

def get_total_memory_mb() -> float:
    """
    Get total system memory usage in MB.

    Returns:
        Memory usage in MB, or 0.0 if psutil not available.
    """
    if not PSUTIL_AVAILABLE:
        return 0.0

    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        return memory_info.rss / (1024 * 1024)  # Convert to MB
    except Exception:
        return 0.0

def check_memory_limit(limit_mb: Optional[float] = None) -> bool:
    """
    Check if current memory usage is within the specified limit.

    Args:
        limit_mb: Memory limit in MB. If None, uses config value.

    Returns:
        True if within limit, False otherwise.
    """
    if limit_mb is None:
        limit_mb = get_memory_limit_mb()

    current_mb = get_total_memory_mb()
    return current_mb <= limit_mb

def validate_memory_within_limit(limit_mb: Optional[float] = None) -> bool:
    """
    Validate that memory usage is within the specified limit.

    Args:
        limit_mb: Memory limit in MB. If None, uses config value.

    Returns:
        True if within limit, False otherwise.
    """
    if limit_mb is None:
        limit_mb = get_memory_limit_mb()

    current_mb = get_total_memory_mb()
    return current_mb <= limit_mb

def _monitor_loop(
    stop_event: threading.Event,
    log_file: Path,
    interval_seconds: float,
    logger: logging.Logger,
):
    """
    Background thread that monitors memory usage.

    Args:
        stop_event: Event to signal thread termination.
        log_file: Path to memory log file.
        interval_seconds: Monitoring interval in seconds.
        logger: Logger instance.
    """
    global _peak_memory_mb

    with open(log_file, "w") as f:
        f.write("timestamp,memory_mb,peak_mb\n")

        while not stop_event.is_set():
            current_mb = get_total_memory_mb()
            _peak_memory_mb = max(_peak_memory_mb, current_mb)

            timestamp = datetime.now().isoformat()
            f.write(f"{timestamp},{current_mb:.2f},{_peak_memory_mb:.2f}\n")
            f.flush()

            logger.debug("Memory monitoring: current=%.2f MB, peak=%.2f MB",
                        current_mb, _peak_memory_mb)

            stop_event.wait(interval_seconds)

@contextmanager
def memory_monitor(
    logger: Optional[logging.Logger] = None,
    limit_mb: Optional[float] = None,
    log_dir: Optional[Path] = None,
):
    """
    Context manager for memory monitoring.

    Args:
        logger: Logger instance.
        limit_mb: Memory limit in MB.
        log_dir: Directory for memory logs.

    Yields:
        None
    """
    global _monitor_thread, _monitor_stop_event, _monitor_log_file, _peak_memory_mb

    if logger is None:
        logger = logging.getLogger("memory_monitor")

    if limit_mb is None:
        limit_mb = get_memory_limit_mb()

    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "data" / "logs"

    # Setup log file
    log_dir.mkdir(parents=True, exist_ok=True)
    _monitor_log_file = log_dir / "memory_monitor.csv"
    _peak_memory_mb = 0.0

    # Start monitoring thread
    _monitor_stop_event = threading.Event()
    _monitor_thread = threading.Thread(
        target=_monitor_loop,
        args=(_monitor_stop_event, _monitor_log_file, _monitor_interval_seconds, logger),
        daemon=True,
    )
    _monitor_thread.start()

    logger.info("Memory monitoring started. Limit: %d MB", limit_mb)

    try:
        yield
    finally:
        # Stop monitoring
        _monitor_stop_event.set()
        if _monitor_thread:
            _monitor_thread.join(timeout=2.0)

        logger.info("Memory monitoring stopped. Peak: %.2f MB", _peak_memory_mb)

def setup_memory_monitoring(
    log_dir: Path,
    logger: Optional[logging.Logger] = None,
    limit_mb: Optional[float] = None,
):
    """
    Setup memory monitoring with a background thread.

    Args:
        log_dir: Directory for memory logs (Path object, not Logger).
        logger: Logger instance.
        limit_mb: Memory limit in MB.

    Note:
        This function now correctly expects a Path object for log_dir,
        not a Logger object. The logger is passed as a separate parameter.
    """
    global _monitor_thread, _monitor_stop_event, _monitor_log_file

    if logger is None:
        logger = logging.getLogger("memory_monitor")

    if limit_mb is None:
        limit_mb = get_memory_limit_mb()

    # Validate log_dir is a Path object
    if not isinstance(log_dir, Path):
        logger.error(
            "setup_memory_monitoring expects log_dir to be a Path object, "
            "not %s", type(log_dir).__name__
        )
        # Try to convert if it's a string
        if isinstance(log_dir, str):
            log_dir = Path(log_dir)
        else:
            raise TypeError(
                f"log_dir must be a Path object, got {type(log_dir).__name__}"
            )

    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)

    # Setup log file
    _monitor_log_file = log_dir / "memory_monitor.csv"
    _peak_memory_mb = 0.0

    # Start monitoring thread
    _monitor_stop_event = threading.Event()
    _monitor_thread = threading.Thread(
        target=_monitor_loop,
        args=(_monitor_stop_event, _monitor_log_file, _monitor_interval_seconds, logger),
        daemon=True,
    )
    _monitor_thread.start()

    logger.info("Memory monitoring started. Limit: %d MB, Log: %s",
               limit_mb, _monitor_log_file)

def get_peak_memory_mb() -> float:
    """
    Get peak memory usage since monitoring started.

    Returns:
        Peak memory in MB.
    """
    return _peak_memory_mb

def stop_memory_monitoring():
    """Stop the memory monitoring thread."""
    global _monitor_thread, _monitor_stop_event

    if _monitor_stop_event:
        _monitor_stop_event.set()

    if _monitor_thread and _monitor_thread.is_alive():
        _monitor_thread.join(timeout=2.0)

    _monitor_thread = None
    _monitor_stop_event = None

def main():
    """Test memory monitoring."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    log_dir = Path(__file__).parent.parent / "data" / "logs"
    setup_memory_monitoring(log_dir, logger)

    logger.info("Simulating work...")
    time.sleep(5)

    logger.info("Peak memory: %.2f MB", get_peak_memory_mb())
    stop_memory_monitoring()

if __name__ == "__main__":
    main()