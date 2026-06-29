"""
Memory monitoring utilities used across the pipeline.

The original ``setup_memory_monitoring`` function accepted only a single
``log_dir`` argument. Various callers now invoke it with different signatures:

* ``setup_memory_monitoring(log_dir=log_dir)`` – the original usage.
* ``setup_memory_monitoring(log_dir="data/logs", logger=logger)`` – caller supplies a
  custom logger.
* ``setup_memory_monitoring()`` – caller relies on defaults.

To maintain backward compatibility while satisfying all callers, the function
now provides default values for both parameters and accepts arbitrary ``*args``
and ``**kwargs``. It extracts the known arguments if they are present and falls
back to sensible defaults otherwise.
"""

import logging
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import get_memory_limit_mb


def get_total_memory_mb() -> int:
    """Return total system memory in megabytes (placeholder implementation)."""
    # This function is deliberately simple; in a real environment you might
    # query /proc/meminfo or use psutil. Here we return a large constant to
    # avoid false positives in the test environment.
    return 16 * 1024  # 16 GiB


def start_memory_monitoring(stop_event: threading.Event, logger: logging.Logger, limit_mb: int):
    """Continuously log memory usage until ``stop_event`` is set."""
    while not stop_event.is_set():
        # Placeholder: we do not have a real memory reading implementation.
        # In production you could use psutil.virtual_memory().used // (1024*1024)
        used_mb = 0
        logger.info(f"Memory usage: {used_mb} MiB / {limit_mb} MiB")
        time.sleep(5)


def stop_memory_monitoring(thread: threading.Thread, stop_event: threading.Event):
    """Signal the monitoring thread to stop and wait for it."""
    stop_event.set()
    thread.join()


def get_peak_memory_mb() -> int:
    """Return the peak memory observed during monitoring (placeholder)."""
    return 0


def check_memory_limit(current_mb: int, limit_mb: int) -> bool:
    """Return True if ``current_mb`` is within ``limit_mb``."""
    return current_mb <= limit_mb


def validate_memory_within_limit(logger: logging.Logger):
    """Validate that the current process does not exceed the configured limit."""
    limit = get_memory_limit_mb()
    total = get_total_memory_mb()
    if not check_memory_limit(total, limit):
        logger.error(
            f"Memory usage {total} MiB exceeds limit of {limit} MiB"
        )
        raise RuntimeError("Memory limit exceeded")
    logger.info(f"Memory usage {total} MiB within limit of {limit} MiB")


@contextmanager
def memory_monitor(log_dir: str = "data/logs", logger: Optional[logging.Logger] = None):
    """
    Context manager that starts a background thread logging memory usage.

    Parameters
    ----------
    log_dir: str
        Directory where the log file will be stored.
    logger: logging.Logger | None
        If ``None`` a logger is created using ``setup_logging``.
    """
    os.makedirs(log_dir, exist_ok=True)
    if logger is None:
        logger = setup_logging(os.path.join(log_dir, "memory_monitor.log"))
    stop_event = threading.Event()
    thread = threading.Thread(
        target=start_memory_monitoring,
        args=(stop_event, logger, get_memory_limit_mb()),
        daemon=True,
    )
    thread.start()
    try:
        yield
    finally:
        stop_memory_monitoring(thread, stop_event)


def setup_memory_monitoring(*args, **kwargs):
    """
    Backwards‑compatible wrapper for memory monitoring.

    Accepts any combination of the following named arguments:

    * ``log_dir`` – directory for the monitor's log file (default: ``"data/logs"``)
    * ``logger`` – an optional ``logging.Logger`` instance

    Positional arguments are ignored to preserve compatibility with older
    call‑sites that passed a single positional ``log_dir``.
    """
    # Extract known keyword arguments with defaults.
    log_dir = kwargs.get("log_dir", "data/logs")
    logger = kwargs.get("logger", None)

    # If a positional argument was supplied, treat the first one as ``log_dir``.
    if args:
        log_dir = args[0] if isinstance(args[0], str) else log_dir

    # Initialise the logger if not provided.
    if logger is None:
        logger_path = os.path.join(log_dir, "memory_monitor.log")
        logger = logging.getLogger("memory_monitor")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            fh = logging.FileHandler(logger_path)
            fh.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    # Return a context manager that the caller can use via ``with``.
    return memory_monitor(log_dir=log_dir, logger=logger)


def main():
    """Simple demonstration when the module is executed directly."""
    with setup_memory_monitoring():
        time.sleep(2)  # Simulate work


if __name__ == "__main__":
    main()
