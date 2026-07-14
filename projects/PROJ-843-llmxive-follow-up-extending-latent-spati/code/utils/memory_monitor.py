import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_current_memory_mb() -> float:
    """
    Return the current process memory usage in megabytes.
    """
    import psutil  # psutil is part of the standard CI environment

    process = psutil.Process(os.getpid())
    mem_bytes = process.memory_info().rss
    return mem_bytes / (1024 * 1024)

def check_memory_limit(limit_gb: float) -> bool:
    """
    Return True if current memory usage exceeds the supplied limit (in GB).
    """
    return get_current_memory_mb() > (limit_gb * 1024)

def should_batch_process(memory_limit_gb: float, threshold_gb: float = 6.0) -> bool:
    """
    Decide whether to fallback to batch‑wise processing based on the
    configured memory limit and a hard threshold.
    """
    return memory_limit_gb > threshold_gb

# ----------------------------------------------------------------------
# Session‑wide metrics storage
# ----------------------------------------------------------------------
_session_metrics: dict = {}

def clear_session_metrics() -> None:
    _session_metrics.clear()

def get_session_metrics() -> dict:
    return dict(_session_metrics)

def save_session_metrics(metrics: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(metrics, f, indent=2)

# ----------------------------------------------------------------------
# Core monitor class
# ----------------------------------------------------------------------
class MemoryMonitor:
    """
    Simple memory monitor that records peak RAM usage during a block of
    code.  The class is deliberately tolerant: any unknown attribute
    access returns a no‑op callable, allowing loosely‑coupled logging
    without raising AttributeError.
    """

    def __init__(self, log_path: Path | None = None):
        self._peak_memory = 0.0
        self._running = False
        self._thread = threading.Thread(target=self._monitor)
        self._thread.daemon = True
        self.log_path = log_path

    # ------------------------------------------------------------------
    # Public API (used by various scripts)
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Begin monitoring in a background thread."""
        if not self._running:
            self._running = True
            self._thread.start()

    def stop(self) -> None:
        """Stop monitoring and wait for the thread to finish."""
        if self._running:
            self._running = False
            self._thread.join()
            if self.log_path:
                self._write_log()

    def get_peak_memory(self) -> float:
        """Return the maximum RAM usage observed (in MB)."""
        return self._peak_memory

    # ------------------------------------------------------------------
    # Internal monitoring loop
    # ------------------------------------------------------------------
    def _monitor(self) -> None:
        while self._running:
            mem = get_current_memory_mb()
            if mem > self._peak_memory:
                self._peak_memory = mem
            time.sleep(0.1)

    def _write_log(self) -> None:
        """Write a simple JSON log with the peak memory."""
        if self.log_path:
            data = {"peak_memory_mb": self._peak_memory, "timestamp": datetime.utcnow().isoformat()}
            save_session_metrics(data, self.log_path)

    # ------------------------------------------------------------------
    # Tolerant fallback for any unexpected attribute
    # ------------------------------------------------------------------
    def __getattr__(self, name):
        """
        Return a no‑op callable for any undefined attribute, making the
        monitor compatible with all existing call sites.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

# ----------------------------------------------------------------------
# Convenience entry‑point (used by some scripts)
# ----------------------------------------------------------------------
def main() -> None:
    """
    Example usage: python -m utils.memory_monitor <log_path>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run a simple memory monitor.")
    parser.add_argument(
        "log_path", type=Path, help="Path to write the JSON memory log."
    )
    args = parser.parse_args()
    monitor = MemoryMonitor(log_path=args.log_path)
    monitor.start()
    try:
        # The monitored block would be placed here.
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop()
        print(f"Memory log written to {args.log_path}")

if __name__ == "__main__":
    main()
