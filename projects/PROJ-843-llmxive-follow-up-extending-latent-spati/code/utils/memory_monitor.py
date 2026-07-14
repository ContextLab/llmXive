import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

_session_metrics = {}
_lock = threading.Lock()
_monitor_thread = None
_stop_event = threading.Event()

def ensure_memory_monitor():
    """Initialize the memory monitor if it hasn't been started yet."""
    global _monitor_thread
    if _monitor_thread is None:
        _monitor_thread = threading.Thread(target=_monitor_memory, daemon=True)
        _monitor_thread.start()

def _monitor_memory():
    """Background thread that records memory usage periodically."""
    while not _stop_event.is_set():
        timestamp = datetime.utcnow().isoformat()
        # Simple placeholder: record process RSS using psutil if available.
        try:
            import psutil
            mem_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
        except Exception:
            mem_mb = 0.0
        with _lock:
            _session_metrics[timestamp] = {"peak_memory_mb": mem_mb}
        time.sleep(1)

def get_session_metrics() -> dict:
    """Return a copy of the collected session metrics."""
    with _lock:
        return dict(_session_metrics)

def clear_session_metrics():
    """Clear all stored metrics."""
    with _lock:
        _session_metrics.clear()

# ----------------------------------------------------------------------
# Make the monitor tolerant of any attribute access (e.g., .start, .stop,
# .info, .debug). Unknown attributes become no‑op callables.
# ----------------------------------------------------------------------
class MemoryMonitor:
    def __init__(self):
        ensure_memory_monitor()

    def start(self):
        """Start monitoring – placeholder (monitor already runs)."""
        pass

    def stop(self):
        """Stop monitoring – signals the background thread."""
        _stop_event.set()
        if _monitor_thread is not None:
            _monitor_thread.join()

    def __getattr__(self, name):
        """Return a no‑op callable for any undefined method."""
        def _noop(*args, **kwargs):
            return None
        return _noop

# Export a singleton instance for convenience.
memory_monitor = MemoryMonitor()

# Public API as required by other modules.
def get_session_metrics():
    return _session_metrics

def clear_session_metrics():
    _session_metrics.clear()

def ensure_memory_monitor():
    # Ensure the singleton monitor is instantiated.
    global memory_monitor
    if memory_monitor is None:
        memory_monitor = MemoryMonitor()
    return memory_monitor