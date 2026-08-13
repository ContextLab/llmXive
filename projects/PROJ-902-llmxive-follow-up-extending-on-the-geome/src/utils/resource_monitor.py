"""
Resource monitoring utility.

This module provides a context manager ``ResourceMonitor`` that records the
peak resident set size (VmRSS) and wall‑clock time of the enclosing code block.
The measured values are available via ``get_metrics`` and can optionally be
written to a JSON file (e.g. ``ci_metrics.json``) when the context exits.

The implementation uses ``psutil`` to query the current process memory usage.
A background thread polls the process at a configurable interval (default:
0.1 seconds) to capture transient memory spikes.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

import psutil

__all__ = ["ResourceMonitor", "monitor_resource"]


class ResourceMonitor:
    """
    Context manager that measures peak RAM usage (VmRSS) and wall‑clock time.

    Parameters
    ----------
    output_path : Path | str | None, optional
        If provided, the measured metrics are written as JSON to this path
        when the context exits. The JSON schema is:
        ``{ "peak_ram_gb": <float>, "wall_clock_min": <float> }``.
    poll_interval : float, optional
        Seconds between successive memory polls. Smaller values give finer
        granularity at the cost of a little more overhead.
    """

    def __init__(
        self,
        output_path: Optional[Path | str] = None,
        *,
        poll_interval: float = 0.1,
    ) -> None:
        self.output_path = Path(output_path) if output_path else None
        self.poll_interval = poll_interval
        self._process = psutil.Process(os.getpid())
        self._peak_rss_bytes: int = 0
        self._start_time: float | None = None
        self._end_time: float | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Context‑manager protocol
    # ------------------------------------------------------------------
    def __enter__(self) -> "ResourceMonitor":
        self._start_time = time.time()
        # Initialise with current RSS
        self._peak_rss_bytes = self._process.memory_info().rss
        # Start background polling thread
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._poll_memory, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        # Stop polling thread
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join()
        self._end_time = time.time()
        # Final check – in case the last poll missed a spike
        current_rss = self._process.memory_info().rss
        if current_rss > self._peak_rss_bytes:
            self._peak_rss_bytes = current_rss

        # Convert to user‑friendly units
        self.peak_ram_gb = self._peak_rss_bytes / (1024**3)
        self.wall_clock_min = (self._end_time - self._start_time) / 60.0

        if self.output_path:
            data: Dict[str, Any] = {
                "peak_ram_gb": self.peak_ram_gb,
                "wall_clock_min": self.wall_clock_min,
            }
            self.output_path.write_text(json.dumps(data, indent=2))

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def get_metrics(self) -> Dict[str, float]:
        """
        Return the measured metrics as a dictionary.

        Returns
        -------
        dict
            ``{ "peak_ram_gb": float, "wall_clock_min": float }``
        """
        return {
            "peak_ram_gb": getattr(self, "peak_ram_gb", 0.0),
            "wall_clock_min": getattr(self, "wall_clock_min", 0.0),
        }

    # ------------------------------------------------------------------
    # Internal implementation
    # ------------------------------------------------------------------
    def _poll_memory(self) -> None:
        """
        Periodically poll the process RSS and keep the maximum observed value.
        """
        while not self._stop_event.is_set():
            rss = self._process.memory_info().rss
            if rss > self._peak_rss_bytes:
                self._peak_rss_bytes = rss
            time.sleep(self.poll_interval)


def monitor_resource(
    func,
    *args,
    output_path: Optional[Path | str] = None,
    poll_interval: float = 0.1,
    **kwargs,
) -> tuple[Any, Dict[str, float]]:
    """
    Convenience wrapper that runs ``func`` while measuring resources.

    Parameters
    ----------
    func : callable
        Function to execute.
    *args, **kwargs : Any
        Arguments forwarded to ``func``.
    output_path : Path | str | None, optional
        If given, a JSON file with the metrics is written after execution.
    poll_interval : float, optional
        Memory‑polling interval in seconds (passed to ``ResourceMonitor``).

    Returns
    -------
    result : Any
        The return value of ``func``.
    metrics : dict
        ``{ "peak_ram_gb": float, "wall_clock_min": float }``.
    """
    with ResourceMonitor(output_path=output_path, poll_interval=poll_interval) as rm:
        result = func(*args, **kwargs)
    return result, rm.get_metrics()
