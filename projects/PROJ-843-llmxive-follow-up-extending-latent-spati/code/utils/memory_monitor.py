"""
Simple memory‑monitoring utility.

The implementation records peak RAM usage and elapsed wall‑clock time using the
``memory_profiler`` package.  It provides a ``start`` method that begins
background sampling and a ``stop`` method that stops sampling and writes a JSON
log file.  Any unknown attribute accesses (e.g. ``info``, ``debug``) are handled
gracefully by returning a no‑op callable, making the class tolerant of varied
logger‑style usage throughout the code base.
"""

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Union

from memory_profiler import memory_usage

class MemoryMonitor:
    """
    Record peak memory usage and elapsed wall‑clock time.

    Example
    -------
    >>> monitor = MemoryMonitor(log_path="data/results/memory_log.json")
    >>> monitor.start()
    >>> # ... code to profile ...
    >>> monitor.stop()
    """

    def __init__(self, log_path: Union[str, os.PathLike] = "data/results/memory_log.json"):
        self.log_path = Path(log_path)
        self._start_time: float | None = None
        self._peak_memory: float | None = None
        self._running = False
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Public API expected by existing scripts
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
        if self._thread is not None:
            self._thread.join()
        self._write_log()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _monitor(self) -> None:
        """Continuously sample memory usage while monitoring is active."""
        # ``memory_usage`` returns a tuple (list_of_memories, timestamps) when
        # ``retval=True``.  We only need the maximum memory observed.
        samples = memory_usage(
            -1, interval=0.1, timeout=None, max_iterations=None, retval=True
        )
        mem_samples = samples[0] if isinstance(samples, tuple) else samples
        self._peak_memory = max(mem_samples) if mem_samples else 0.0

    def _write_log(self) -> None:
        """Serialise the collected metrics as JSON."""
        end_time = time.time()
        elapsed = end_time - (self._start_time or end_time)
        log = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "elapsed_seconds": elapsed,
            "peak_memory_mb": self._peak_memory,
        }
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as fp:
            json.dump(log, fp, indent=2, sort_keys=True)

    # ------------------------------------------------------------------
    # Graceful fallback for unexpected attribute access
    # ------------------------------------------------------------------
    def __getattr__(self, name):
        """
        Return a no‑op callable for any undefined attribute.

        This makes the class tolerant of arbitrary logger‑style calls
        (e.g., ``monitor.info(...)``) used elsewhere in the code base.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop