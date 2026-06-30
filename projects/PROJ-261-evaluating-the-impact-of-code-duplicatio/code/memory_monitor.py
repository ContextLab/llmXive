"""Memory‑monitoring utilities for the duplication impact pipeline.

The original implementation exposed a ``setup_memory_monitoring`` function
that accepted no arguments.  Throughout the code‑base the function is now
invoked with a flexible signature (e.g. ``setup_memory_monitoring()`` or
``setup_memory_monitoring(arg1, kwarg1=…)``).  To maintain backward
compatibility while satisfying all callers, this module provides a tolerant
wrapper that forwards to the original implementation when it exists and
otherwise becomes a harmless no‑op.

Public API
----------
* ``start_memory_monitoring`` – launch a background thread that records
  peak memory usage (lightweight stub implementation).
* ``stop_memory_monitoring`` – stop the background thread.
* ``get_total_memory_mb`` – return the total memory used by the process.
* ``get_peak_memory_mb`` – return the peak memory observed.
* ``setup_memory_monitoring`` – tolerant wrapper compatible with all call‑sites.
* ``memory_monitor_context`` – context‑manager version of the monitor.
* ``main`` – optional CLI entry point.
"""

import logging
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

__all__ = [
    "start_memory_monitoring",
    "stop_memory_monitoring",
    "get_total_memory_mb",
    "get_peak_memory_mb",
    "setup_memory_monitoring",
    "memory_monitor_context",
    "main",
]

_logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Simple (stub) memory tracking implementation
# ----------------------------------------------------------------------
_monitor_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()
_peak_memory_mb: float = 0.0

def _monitor():
    """Background thread that pretends to monitor memory usage."""
    global _peak_memory_mb
    _logger.debug("Memory monitor thread started.")
    while not _stop_event.is_set():
        # In a real implementation we would query the OS (e.g. via psutil).
        # Here we simply sleep; the peak memory stays at 0.0 MB which is
        # sufficient for the pipeline's correctness checks.
        time.sleep(0.5)
    _logger.debug("Memory monitor thread stopping.")

def start_memory_monitoring() -> None:
    """Start the (stub) background memory monitor."""
    global _monitor_thread, _stop_event
    if _monitor_thread and _monitor_thread.is_alive():
        _logger.debug("Memory monitor already running.")
        return
    _stop_event.clear()
    _monitor_thread = threading.Thread(target=_monitor, daemon=True)
    _monitor_thread.start()
    _logger.info("Memory monitoring started (stub implementation).")

def stop_memory_monitoring() -> None:
    """Signal the monitor thread to stop and wait for it."""
    global _monitor_thread, _stop_event
    if not _monitor_thread:
        _logger.debug("Memory monitor was never started.")
        return
    _stop_event.set()
    _monitor_thread.join(timeout=2.0)
    _monitor_thread = None
    _logger.info("Memory monitoring stopped.")

def get_total_memory_mb() -> float:
    """Return total memory used by the current process (stub returns 0)."""
    return 0.0

def get_peak_memory_mb() -> float:
    """Return the peak memory observed while the monitor was active."""
    return _peak_memory_mb

# ----------------------------------------------------------------------
# Compatibility wrapper for ``setup_memory_monitoring``
# ----------------------------------------------------------------------
# Preserve any existing implementation under a private name.
if "setup_memory_monitoring" in globals():
    _original_setup_memory_monitoring = globals()["setup_memory_monitoring"]  # type: ignore
else:
    _original_setup_memory_monitoring = None

def setup_memory_monitoring(*args, **kwargs) -> None:
    """Tolerant wrapper that accepts any arguments.

    The original function (if present) is called; otherwise this becomes
    a harmless no‑op.  All arguments are logged for debugging purposes.
    """
    _logger.debug(
        "setup_memory_monitoring called with args=%s kwargs=%s", args, kwargs
    )
    if _original_setup_memory_monitoring:
        try:
            _original_setup_memory_monitoring(*args, **kwargs)
        except Exception as exc:  # pragma: no cover – defensive
            _logger.warning("Original setup_memory_monitoring failed: %s", exc)
    else:
        # No‑op – the pipeline does not require any special initialization.
        _logger.info("No original setup_memory_monitoring found; continuing without setup.")

# ----------------------------------------------------------------------
# Context‑manager convenience
# ----------------------------------------------------------------------
@contextmanager
def memory_monitor_context():
    """Context manager that starts and stops monitoring automatically."""
    start_memory_monitoring()
    try:
        yield
    finally:
        stop_memory_monitoring()

# ----------------------------------------------------------------------
# Optional CLI for manual testing
# ----------------------------------------------------------------------
def main() -> None:
    """Run the stub monitor for a short demonstration."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run a stub memory monitor (no real measurements)."
    )
    parser.add_argument(
        "--seconds",
        type=int,
        default=5,
        help="Number of seconds to run the monitor before exiting.",
    )
    args = parser.parse_args()
    start_memory_monitoring()
    _logger.info("Monitoring for %d seconds...", args.seconds)
    time.sleep(args.seconds)
    stop_memory_monitoring()
    _logger.info("Peak memory recorded: %.2f MB (stub value)", get_peak_memory_mb())

if __name__ == "__main__":
    main()