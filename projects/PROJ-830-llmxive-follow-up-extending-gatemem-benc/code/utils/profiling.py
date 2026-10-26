"""
Profiling utilities for measuring function latency and peak RAM usage.

This module provides a set of helpers used throughout the project to
profile execution time (in milliseconds) and peak memory consumption
(in megabytes) of arbitrary callables. The implementation relies on
``psutil`` for process memory introspection and the standard ``time``
module for timing. All functions return plain ``dict`` objects with a
standardized set of keys: ``latency_ms`` and ``peak_ram_mb``.
"""

import json
import time
import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import psutil
import numpy as np
from contextlib import contextmanager

# Global process handle and peak memory tracker
_process = psutil.Process(os.getpid())
_peak_memory_mb: float = 0.0


def _update_peak_memory(current_mb: float) -> None:
    """Update the global peak memory measurement."""
    global _peak_memory_mb
    if current_mb > _peak_memory_mb:
        _peak_memory_mb = current_mb


def get_process_memory_mb() -> float:
    """
    Return the current resident set size (RSS) of the process in megabytes.

    Returns
    -------
    float
        Current memory usage in MB.
    """
    rss_bytes = _process.memory_info().rss
    return rss_bytes / (1024 * 1024)


def get_peak_memory_mb() -> float:
    """
    Return the highest memory usage observed during the most recent
    profiling session.

    Returns
    -------
    float
        Peak memory usage in MB.
    """
    return _peak_memory_mb


def reset_profiling() -> None:
    """
    Reset the internal peak‑memory counter. Should be called before a
    new profiling session begins.
    """
    global _peak_memory_mb
    _peak_memory_mb = 0.0


def start_profiling() -> Dict[str, Any]:
    """
    Begin a profiling block.

    Returns
    -------
    dict
        Context dictionary containing the start time (seconds since epoch)
        and a placeholder for any additional metadata.
    """
    reset_profiling()
    start_time = time.time()
    # Record initial memory as a baseline for peak calculation
    _update_peak_memory(get_process_memory_mb())
    return {"start_time": start_time}


def stop_profiling(start_time: float) -> Dict[str, float]:
    """
    End a profiling block started with :func:`start_profiling`.

    Parameters
    ----------
    start_time: float
        The ``start_time`` value returned by ``start_profiling``.

    Returns
    -------
    dict
        Dictionary with ``latency_ms`` and ``peak_ram_mb``.
    """
    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000.0

    # Update peak memory with the final measurement
    _update_peak_memory(get_process_memory_mb())

    return {"latency_ms": latency_ms, "peak_ram_mb": get_peak_memory_mb()}


def profile_execution(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Dict[str, float]:
    """
    Profile the execution of a callable.

    Parameters
    ----------
    func : callable
        The function to execute.
    *args, **kwargs :
        Arguments forwarded to ``func``.

    Returns
    -------
    dict
        Profiling result containing ``latency_ms`` and ``peak_ram_mb``.
    """
    ctx = start_profiling()
    # Execute the target function
    func(*args, **kwargs)
    return stop_profiling(ctx["start_time"])


@dataclass
class ProfileResult:
    """
    Simple data container for profiling results.
    """
    latency_ms: float
    peak_ram_mb: float


@contextmanager
def profile_block(label: str) -> Any:
    """
    Context manager for profiling an arbitrary code block.

    Parameters
    ----------
    label : str
        Human‑readable identifier for the block (exposed via the context).

    Yields
    ------
    dict
        Context dict containing the ``label`` and the ``start_time``.
    """
    ctx = {"label": label, "start_time": time.time()}
    # Record initial memory
    _update_peak_memory(get_process_memory_mb())
    try:
        yield ctx
    finally:
        # On exit compute and store profiling info in the context
        latency_ms = (time.time() - ctx["start_time"]) * 1000.0
        _update_peak_memory(get_process_memory_mb())
        ctx["latency_ms"] = latency_ms
        ctx["peak_ram_mb"] = get_peak_memory_mb()


def profile_function(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that profiles a function but returns the original result.

    The profiling data is attached to the wrapped function as the
    ``_profile_result`` attribute (a :class:`ProfileResult` instance).

    Parameters
    ----------
    func : callable
        Function to be wrapped.

    Returns
    -------
    callable
        Wrapped function.
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.time()
        _update_peak_memory(get_process_memory_mb())
        result = func(*args, **kwargs)
        latency_ms = (time.time() - start) * 1000.0
        _update_peak_memory(get_process_memory_mb())
        profile_res = ProfileResult(latency_ms=latency_ms, peak_ram_mb=get_peak_memory_mb())
        # Attach profiling result to the wrapper for introspection
        wrapper._profile_result = profile_res  # type: ignore[attr-defined]
        return result

    return wrapper


class ProfileContext:
    """
    Context manager class that mimics the behaviour of ``profile_block``
    but exposes a ``get_result`` method returning a :class:`ProfileResult`.
    """

    def __init__(self) -> None:
        self._start_time: Optional[float] = None
        self._result: Optional[ProfileResult] = None

    def __enter__(self) -> "ProfileContext":
        reset_profiling()
        self._start_time = time.time()
        _update_peak_memory(get_process_memory_mb())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._start_time is None:
            return
        latency_ms = (time.time() - self._start_time) * 1000.0
        _update_peak_memory(get_process_memory_mb())
        self._result = ProfileResult(latency_ms=latency_ms, peak_ram_mb=get_peak_memory_mb())

    def get_result(self) -> ProfileResult:
        """
        Return the profiling result after the context has exited.

        Raises
        ------
        RuntimeError
            If called before the context manager has been exited.
        """
        if self._result is None:
            raise RuntimeError("Profiling result is not available yet; ensure the context has exited.")
        return self._result


def get_results_summary(results: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Compute summary statistics for a list of profiling result dictionaries.

    Parameters
    ----------
    results : list of dict
        Each dict must contain ``latency_ms`` and ``peak_ram_mb``.

    Returns
    -------
    dict
        Summary containing mean, std, min, and max for both metrics.
        Keys follow the pattern ``<metric>_ms_<stat>`` or
        ``peak_ram_mb_<stat>``.
    """
    if not results:
        return {
            "latency_ms_mean": 0.0,
            "latency_ms_std": 0.0,
            "latency_ms_min": 0.0,
            "latency_ms_max": 0.0,
            "peak_ram_mb_mean": 0.0,
            "peak_ram_mb_std": 0.0,
            "peak_ram_mb_min": 0.0,
            "peak_ram_mb_max": 0.0,
        }

    latency_vals = np.array([r["latency_ms"] for r in results], dtype=float)
    ram_vals = np.array([r["peak_ram_mb"] for r in results], dtype=float)

    summary = {
        "latency_ms_mean": float(np.mean(latency_vals)),
        "latency_ms_std": float(np.std(latency_vals, ddof=0)),
        "latency_ms_min": float(np.min(latency_vals)),
        "latency_ms_max": float(np.max(latency_vals)),
        "peak_ram_mb_mean": float(np.mean(ram_vals)),
        "peak_ram_mb_std": float(np.std(ram_vals, ddof=0)),
        "peak_ram_mb_min": float(np.min(ram_vals)),
        "peak_ram_mb_max": float(np.max(ram_vals)),
    }
    return summary


def save_results_to_file(results: Dict[str, Any], output_path: str) -> None:
    """
    Serialize profiling results to a JSON file.

    Parameters
    ----------
    results : dict
        Profiling result dictionary (e.g., output of ``profile_execution``).
    output_path : str
        Destination file path. Parent directories are created automatically.
    """
    from pathlib import Path

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True)