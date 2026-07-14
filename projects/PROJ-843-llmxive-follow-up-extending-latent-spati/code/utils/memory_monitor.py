"""
Simple memory‑monitoring utility.

The implementation records the start and stop timestamps, optionally samples
peak RAM usage using ``memory_profiler`` (if available), and writes a JSON
log with the collected metrics.  The class is deliberately tolerant of
arbitrary logging‑style method calls (e.g. ``.info()``, ``.debug()``) by
providing a ``__getattr__`` fallback that returns a no‑op callable.  This
makes it safe to use the same instance across the entire code base without
having to keep the exact method list in sync.
"""

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Union

try:
    # ``memory_profiler`` is optional – if unavailable we fall back to a
    # no‑op implementation.
    from memory_profiler import memory_usage
except Exception:  # pragma: no cover
    memory_usage = None  # type: ignore

class MemoryMonitor:
    """
    Minimal memory‑monitor that records peak RAM usage (if possible) and the
    total wall‑clock time of a code block.

    The monitor can be used as a context manager or via explicit ``start`` /
    ``stop`` calls.  Any unknown attribute access returns a no‑op callable
    to keep the API tolerant across the codebase.
    """

    def __init__(self, output_path: Union[str, Path] = None):
        """
        Parameters
        ----------
        output_path: Union[str, Path], optional
            Destination for the JSON log.  If omitted, ``memory.log`` will be
            created in the current working directory.
        """
        self._output_path = Path(output_path) if output_path else None
        self._start_time: float = 0.0
        self._end_time: float = 0.0
        self._peak_mem: float = 0.0
        self._thread: threading.Thread = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Begin timing and (if possible) start RAM sampling."""
        self._start_time = time.time()
        if memory_usage:
            # Run memory sampling in a background thread.
            self._thread = threading.Thread(
                target=self._sample_memory, daemon=True
            )
            self._thread.start()

    def stop(self) -> None:
        """Stop timing, terminate sampling, and write the log."""
        self._end_time = time.time()
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join()
        self._write_log()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _sample_memory(self) -> None:
        """Continuously sample memory usage until ``_stop_event`` is set."""
        while not self._stop_event.is_set():
            try:
                # ``memory_usage`` returns a list of samples; we take the first.
                current = memory_usage(-1, interval=0.1, timeout=0.1)[0]  # type: ignore
                self._peak_mem = max(self._peak_mem, current)
            except Exception:
                # If ``memory_usage`` fails for any reason, we simply ignore.
                pass

    def _write_log(self) -> None:
        """Write a JSON log containing duration and peak RAM (if measured)."""
        if not self._output_path:
            # Default log location – a ``memory.log`` file next to the caller.
            self._output_path = Path("memory.log")
        log_data = {
            "duration_seconds": self._end_time - self._start_time,
            "peak_ram_mb": self._peak_mem,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        try:
            self._output_path.parent.mkdir(parents=True, exist_ok=True)
            with self._output_path.open("w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2)
        except Exception as exc:
            # Logging failures must not crash the main pipeline.
            print(f"[MemoryMonitor] Failed to write log: {exc}")

    # ------------------------------------------------------------------
    # Compatibility shim – any unknown attribute becomes a no‑op callable.
    # ------------------------------------------------------------------
    def __getattr__(self, name: str):
        def _noop(*args, **kwargs):
            return None

        return _noop

    # ------------------------------------------------------------------
    # Context‑manager support
    # ------------------------------------------------------------------
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        # Do not suppress exceptions.
        return False
