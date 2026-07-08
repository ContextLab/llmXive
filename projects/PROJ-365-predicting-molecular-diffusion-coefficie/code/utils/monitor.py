"""
utils.monitor
----------------
Utility for enforcing runtime and memory usage limits on functions.
Provides:
- ``ResourceLimitExceeded`` exception
- ``ResourceMonitor`` class (context manager) that records total runtime and peak memory
  and writes a JSON report to ``data/artifacts/reports/runtime_memory.json``.
- ``enforce_limits`` helper for direct limit checks.
- ``run_with_limits`` convenience wrapper that runs a callable under the limits.
"""

import json
import os
import signal
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

import psutil

# -------------------------------------------------------------------------
# Configuration constants (can be overridden in tests)
# -------------------------------------------------------------------------
DEFAULT_TIME_LIMIT_SECONDS = 6 * 60 * 60  # 6 hours
DEFAULT_MEMORY_LIMIT_MB = 7 * 1024       # 7 GB in megabytes

# -------------------------------------------------------------------------
# Exception
# -------------------------------------------------------------------------
class ResourceLimitExceeded(Exception):
    """Raised when a runtime or memory limit is exceeded."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

# -------------------------------------------------------------------------
# Helper to enforce limits given measured values
# -------------------------------------------------------------------------
def enforce_limits(
    elapsed_seconds: float,
    peak_memory_mb: float,
    time_limit: float = DEFAULT_TIME_LIMIT_SECONDS,
    memory_limit: float = DEFAULT_MEMORY_LIMIT_MB,
) -> None:
    """
    Check elapsed time and peak memory against provided limits.
    Raises ``ResourceLimitExceeded`` with a descriptive message if any limit is broken.
    """
    exceeded = []
    if elapsed_seconds > time_limit:
        exceeded.append(f"time limit ({time_limit:.2f}s) exceeded (actual: {elapsed_seconds:.2f}s)")
    if peak_memory_mb > memory_limit:
        exceeded.append(
            f"memory limit ({memory_limit:.2f} MB) exceeded (actual: {peak_memory_mb:.2f} MB)"
        )
    if exceeded:
        raise ResourceLimitExceeded("; ".join(exceeded))

# -------------------------------------------------------------------------
# Context manager that records runtime and memory usage
# -------------------------------------------------------------------------
class ResourceMonitor:
    """
    Context manager that monitors total runtime and peak RSS memory usage.
    Upon exit it writes a JSON report to ``data/artifacts/reports/runtime_memory.json``.
    """

    def __init__(
        self,
        time_limit: float = DEFAULT_TIME_LIMIT_SECONDS,
        memory_limit: float = DEFAULT_MEMORY_LIMIT_MB,
    ):
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.peak_memory_mb: float = 0.0
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.process = psutil.Process(os.getpid())

    # -------------------------------------------------------------
    def __enter__(self) -> "ResourceMonitor":
        self.start_time = time.time()
        self._monitor_thread = threading.Thread(target=self._monitor_memory, daemon=True)
        self._monitor_thread.start()
        return self

    # -------------------------------------------------------------
    def __exit__(self, exc_type, exc_val, exc_tb) -> Optional[bool]:
        self.end_time = time.time()
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join()

        total_seconds = self.end_time - self.start_time if self.start_time else 0.0
        # Write JSON report
        report = {
            "total_seconds": total_seconds,
            "peak_memory_mb": self.peak_memory_mb,
        }
        report_path = Path("data/artifacts/reports/runtime_memory.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as fp:
            json.dump(report, fp, indent=2)

        # If an exception was raised inside the block we let it propagate.
        # Otherwise we enforce the limits here.
        if exc_type is None:
            try:
                enforce_limits(
                    elapsed_seconds=total_seconds,
                    peak_memory_mb=self.peak_memory_mb,
                    time_limit=self.time_limit,
                    memory_limit=self.memory_limit,
                )
            except ResourceLimitExceeded as e:
                # Re‑raise after writing the report so callers can catch it.
                raise e
        # Returning False propagates any exception (if present)
        return False

    # -------------------------------------------------------------
    def _monitor_memory(self) -> None:
        """
        Background thread that polls the process RSS memory and records the peak.
        """
        while not self._stop_event.is_set():
            try:
                mem_bytes = self.process.memory_info().rss
                mem_mb = mem_bytes / (1024 * 1024)
                if mem_mb > self.peak_memory_mb:
                    self.peak_memory_mb = mem_mb
            except Exception:
                # In extremely rare cases psutil may fail; ignore and continue.
                pass
            time.sleep(0.1)  # poll interval

# -------------------------------------------------------------------------
# Convenience wrapper
# -------------------------------------------------------------------------
def run_with_limits(
    func: Callable[..., Any],
    *args,
    time_limit: float = DEFAULT_TIME_LIMIT_SECONDS,
    memory_limit: float = DEFAULT_MEMORY_LIMIT_MB,
    **kwargs,
) -> Any:
    """
    Execute ``func`` under the configured runtime and memory limits.
    Returns whatever ``func`` returns, or raises ``ResourceLimitExceeded``.
    """
    with ResourceMonitor(time_limit=time_limit, memory_limit=memory_limit) as monitor:
        result = func(*args, **kwargs)
    # If the context manager did not raise, limits were respected.
    return result
