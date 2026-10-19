"""
Utility module providing a robust ResourceMonitor for the pipeline.

Features:
* get_logger(name) – returns a logger configured with INFO level and a file
  handler writing to ``results/pipeline.log``.
* MemoryLimitExceeded – exception raised when a step exceeds the configured
  memory limit.
* ResourceMonitor – class with a ``run(step_name, fn, *args, **kwargs)`` method
  that measures wall‑time and peak RSS (via ``psutil``) while the supplied
  callable executes, aborts on memory overflow and records the metrics to
  ``results/monitoring.csv`` (header created on first write).
* __main__ self‑test – executes a trivial computation through the monitor
  and prints a confirmation message, thereby creating ``results/monitoring.csv``.
"""

import csv
import time
import threading
from pathlib import Path
from typing import Any, Callable, Optional

import psutil

from llmxive_toolkit import paths, get_logger as toolkit_get_logger
from code.config import Config

# ----------------------------------------------------------------------
# Logger helper
# ----------------------------------------------------------------------
def get_logger(name: str):
    """
    Return a logger configured with INFO level and a file handler that writes
    to ``results/pipeline.log``. The underlying ``llmxive_toolkit`` logger is
    reused for consistency across the project.
    """
    log_file = paths.results("pipeline.log")
    return toolkit_get_logger(name, log_file=str(log_file))

# ----------------------------------------------------------------------
# Exception signalling memory limit breach
# ----------------------------------------------------------------------
class MemoryLimitExceeded(Exception):
    """Raised when the observed peak RSS exceeds the configured memory limit."""
    pass

# ----------------------------------------------------------------------
# Core monitoring class
# ----------------------------------------------------------------------
class ResourceMonitor:
    """
    Context‑free resource monitor.  Use ``run`` to execute a callable while
    measuring wall‑time and peak resident set size (RSS).  After execution a
    CSV line ``step_name,wall_time_s,peak_ram_bytes`` is appended to
    ``results/monitoring.csv``.
    """

    _csv_header = ["step_name", "wall_time_s", "peak_ram_bytes"]

    def __init__(self):
        # Resolve the CSV path lazily – it will be created on first write.
        self._csv_path = paths.results("monitoring.csv")
        self._csv_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_header(self):
        """Write the CSV header if the file does not yet exist or is empty."""
        if not self._csv_path.exists() or self._csv_path.stat().st_size == 0:
            with self._csv_path.open("w", newline="") as fp:
                writer = csv.writer(fp)
                writer.writerow(self._csv_header)

    def _record(self, step_name: str, wall_time_s: float, peak_ram_bytes: int):
        """Append a single metric row to the CSV."""
        self._ensure_header()
        with self._csv_path.open("a", newline="") as fp:
            writer = csv.writer(fp)
            writer.writerow([step_name, f"{wall_time_s:.6f}", peak_ram_bytes])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, step_name: str, fn: Callable[..., Any], *args, **kwargs) -> Any:
        """
        Execute ``fn(*args, **kwargs)`` while sampling RSS every 0.5 s.

        Parameters
        ----------
        step_name: str
            Identifier written to the monitoring CSV.
        fn: Callable
            The function to be monitored.
        *args, **kwargs:
            Arguments forwarded to ``fn``.

        Returns
        -------
        The return value of ``fn`` (if it completes without raising).

        Raises
        ------
        MemoryLimitExceeded
            If the observed peak RSS exceeds ``config.MEMORY_LIMIT_BYTES``.
        Exception
            Propagates any exception raised by ``fn``.
        """
        logger = get_logger(__name__)

        # Prepare monitoring
        process = psutil.Process()
        peak_rss = 0  # bytes
        start_time = time.time()

        # Run the target function in a separate thread so we can poll memory.
        result_container: list[Optional[Any]] = [None]
        exception_container: list[Optional[BaseException]] = [None]

        def _target():
            try:
                result_container[0] = fn(*args, **kwargs)
            except BaseException as exc:  # capture any exception
                exception_container[0] = exc

        thread = threading.Thread(target=_target, daemon=True)
        thread.start()

        # Periodic sampling loop
        while thread.is_alive():
            try:
                rss = process.memory_info().rss
                if rss > peak_rss:
                    peak_rss = rss
            except Exception as e:
                logger.debug(f"Failed to read RSS: {e}")
            time.sleep(0.5)

        # One final sample after the thread has finished
        try:
            rss = process.memory_info().rss
            if rss > peak_rss:
                peak_rss = rss
        except Exception:
            pass

        wall_time = time.time() - start_time

        # Memory‑limit check
        limit_bytes = getattr(Config, "MEMORY_LIMIT_BYTES", 7 * 1024 ** 3)  # 7 GB default
        if peak_rss > limit_bytes:
            logger.error(
                f"Memory limit exceeded for step '{step_name}': "
                f"{peak_rss} bytes > {limit_bytes} bytes"
            )
            # Record the offending measurement before raising
            self._record(step_name, wall_time, peak_rss)
            raise MemoryLimitExceeded(
                f"Peak RSS {peak_rss} exceeds limit of {limit_bytes} bytes"
            )

        # Record successful metrics
        self._record(step_name, wall_time, peak_rss)

        # Propagate any exception from the target function
        if exception_container[0] is not None:
            raise exception_container[0]

        return result_container[0]

# ----------------------------------------------------------------------
# Self‑test entry point
# ----------------------------------------------------------------------
def _self_test():
    """
    Run a trivial computation through ``ResourceMonitor.run`` to verify
    functionality and generate ``results/monitoring.csv`` with a single
    entry.
    """
    monitor = ResourceMonitor()

    def trivial():
        # Simple workload that uses a tiny amount of memory and CPU.
        total = 0
        for i in range(10_000):
            total += i * i
        return total

    # Execute under monitoring
    monitor.run("selftest", trivial)

    print("ResourceMonitor self-test OK")

if __name__ == "__main__":
    _self_test()