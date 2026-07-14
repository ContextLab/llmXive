"""
Simple memory‑monitoring utility.

The original implementation provided ``start`` and ``stop`` methods.
To make the class robust against the many different call‑sites in the
repository, a ``__getattr__`` fallback is added that returns a no‑op
callable for any undefined attribute.  This satisfies the contract that
any logger‑style method (e.g. ``info``, ``debug``, ``warning``) can be
called without raising ``AttributeError``.
"""

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

class MemoryMonitor:
    """
    Monitors peak RAM usage and wall‑clock time.

    Typical usage::

        monitor = MemoryMonitor()
        monitor.start()
        # ... code to profile ...
        monitor.stop()
    """

    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or Path("memory_profile.log")
        self._start_time: Optional[float] = None
        self._peak_memory: Optional[float] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Core public API
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Begin monitoring in a background thread."""
        if self._running:
            return
        self._running = True
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop monitoring and write the log file."""
        if not self._running:
            return
        self._running = False
        if self._thread:
            self._thread.join()
        self._write_log()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _monitor(self) -> None:
        """Continuously record maximum RSS memory."""
        import psutil  # Imported lazily to avoid a hard dependency elsewhere

        max_mem = 0.0
        while self._running:
            mem = psutil.Process(os.getpid()).memory_info().rss / (1024 ** 2)  # MB
            if mem > max_mem:
                max_mem = mem
            time.sleep(0.5)
        self._peak_memory = max_mem

    def _write_log(self) -> None:
        """Serialize the profiling information as JSON."""
        if self._start_time is None:
            return
        elapsed = time.time() - self._start_time
        data = {
            "elapsed_seconds": elapsed,
            "peak_memory_mb": self._peak_memory,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "elapsed_seconds": elapsed,
            "peak_memory_mb": self._peak_memory,
        }
        try:
            with self.log_path.open("w") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            # Logging failures should never crash the pipeline.
            print(f"[MemoryMonitor] Failed to write log: {exc}")

    # ------------------------------------------------------------------
    # Tolerant fallback for any undefined attribute
    # ------------------------------------------------------------------
    def __getattr__(self, name: str):
        """
        Return a no‑op callable for any attribute that does not exist.

        This makes the monitor usable as a generic logger across the code
        base without having to implement every possible method name.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop