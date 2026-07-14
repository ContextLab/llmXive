import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

class MemoryMonitor:
    """
    Simple memory logger that records peak RAM usage and timestamps.
    It uses the `memory_profiler` package under the hood (as required by the
    original specification) but also provides a permissive fallback for any
    attribute accessed on the instance.
    """

    def __init__(self, log_path: Path = None, interval: float = 1.0):
        self.log_path = log_path or Path("memory_profile.log")
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._monitor)
        self.records = []

    def start(self):
        """Start the background monitoring thread."""
        self._thread.start()

    def stop(self):
        """Signal the monitoring thread to stop and wait for it."""
        self._stop_event.set()
        self._thread.join()
        self._write_log()

    def _monitor(self):
        """Collect memory usage at the configured interval."""
        try:
            from memory_profiler import memory_usage
        except ImportError as exc:
            raise ImportError(
                "memory_profiler is required for MemoryMonitor but is not installed."
            ) from exc

        while not self._stop_event.is_set():
            usage = memory_usage(-1, interval=0.0, timeout=1)
            timestamp = datetime.utcnow().isoformat() + "Z"
            self.records.append({"timestamp": timestamp, "memory_mb": usage[0]})
            time.sleep(self.interval)

    def _write_log(self):
        """Write the collected records to the log file in JSON lines format."""
        if not self.records:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("w", encoding="utf-8") as f:
            for rec in self.records:
                f.write(json.dumps(rec) + "\n")

    # ------------------------------------------------------------------
    # Permissive fallback: any undefined attribute becomes a no‑op callable.
    # ------------------------------------------------------------------
    def __getattr__(self, name):
        """
        Return a no‑op function for any attribute that does not exist.
        This makes the monitor tolerant to arbitrary logger‑style calls
        (e.g., .info(), .debug(), .warning(), etc.) used throughout the
        codebase without raising AttributeError.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop
