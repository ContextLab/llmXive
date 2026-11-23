"""
memory_monitor.py
------------------

Simple RAM-limit wrapper based on ``tracemalloc``.
Provides ``MemoryLimitError`` and a ``run_with_limit`` helper that executes a
callable while monitoring peak memory usage. If the peak exceeds the supplied
limit (in GB) a ``MemoryLimitError`` is raised.
"""

import tracemalloc
from typing import Any, Callable


class MemoryLimitError(RuntimeError):
    """Raised when the observed peak memory usage exceeds the allowed limit."""


def run_with_limit(limit_gb: float, func: Callable[..., Any], *args, **kwargs) -> Any:
    """
    Execute *func* with the provided arguments while monitoring memory usage.

    Parameters
    ----------
    limit_gb: float
        Maximum allowed peak memory usage in gigabytes.
    func: Callable
        The function to execute.
    *args, **kwargs:
        Arguments forwarded to *func*.

    Returns
    -------
    Any
        The return value from *func* if the memory limit is not breached.

    Raises
    -------
    MemoryLimitError
        If the observed peak memory usage exceeds *limit_gb*.
    """
    tracemalloc.start()
    try:
        result = func(*args, **kwargs)
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_gb = peak / (1024 ** 3)  # convert bytes to gigabytes
        if peak_gb > limit_gb:
            raise MemoryLimitError(
                f"Peak memory usage {peak_gb:.2f} GB exceeds limit of {limit_gb:.2f} GB"
            )
    return result