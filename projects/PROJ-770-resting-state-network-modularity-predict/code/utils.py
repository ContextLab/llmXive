"""
utils.py
=========

Utility helpers for the resting‑state network modularity project.

This module provides two kinds of functionality that are needed across
many pipeline scripts:

1. **Global random seed handling** – ensures reproducibility of NumPy
   and the standard library ``random`` module.  The function is tiny but
   centralised so that every script can simply call ``set_global_seed`` at
   the top of its ``main`` function.

2. **Memory profiling helpers** – lightweight utilities that report the
   current and peak memory usage of the Python process.  They are used in
   tests and can be wrapped around expensive functions with the
   ``@memory_profile`` decorator.

The implementation relies only on the standard library and the
``psutil`` package, which is guaranteed to be available in the execution
environment (see the platform description).  All functions are type‑annotated
and include docstrings for clarity.
"""

from __future__ import annotations

import os
import random
import functools
import logging
from typing import Callable, Any, TypeVar, cast

import numpy as np
import psutil

__all__ = [
    "set_global_seed",
    "get_current_memory_mb",
    "get_peak_memory_mb",
    "memory_profile",
]

# Configure a module‑level logger.  Scripts can obtain a child logger via
# ``logging.getLogger(__name__)`` if they need more detailed messages.
_logger = logging.getLogger(__name__)
if not _logger.handlers:
    # Attach a simple console handler if the importing script has not
    # configured logging yet.
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s – %(message)s"
    )
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)

T = TypeVar("T", bound=Callable[..., Any])


def set_global_seed(seed: int) -> None:
    """
    Set the random seed for reproducibility across NumPy, ``random`` and,
    where possible, the Python hash seed.

    Parameters
    ----------
    seed : int
        The integer seed to use.  It will be passed to ``numpy.random.seed``
        and ``random.seed``.  In addition, the environment variable
        ``PYTHONHASHSEED`` is set – this influences the hash randomisation
        used by Python for dict/set ordering.  Changing this variable after
        the interpreter has started has no effect, but setting it here
        makes the intent explicit for callers that may spawn subprocesses.
    """
    _logger.debug("Setting global random seed to %s", seed)
    np.random.seed(seed)
    random.seed(seed)
    # Setting PYTHONHASHSEED after interpreter start does not affect the
    # current process, but it is useful for child processes that may be
    # spawned later (e.g., via multiprocessing).
    os.environ["PYTHONHASHSEED"] = str(seed)


def _process() -> psutil.Process:
    """
    Helper that returns a ``psutil.Process`` object for the current process.
    Cached for speed – ``psutil`` is lightweight for a single process.
    """
    return psutil.Process(os.getpid())


def get_current_memory_mb() -> float:
    """
    Return the current resident set size (RSS) of the Python process in
    megabytes.

    This is the amount of memory the process is actively using.  It is a
    convenient metric for quick sanity checks in tests or logs.

    Returns
    -------
    float
        Current memory usage in MB.
    """
    mem_bytes = _process().memory_info().rss
    mem_mb = mem_bytes / (1024 ** 2)
    _logger.debug("Current memory usage: %.2f MB", mem_mb)
    return mem_mb


def get_peak_memory_mb() -> float:
    """
    Return the peak (high‑water mark) memory usage of the process in
    megabytes.

    On Linux the ``peak_wset`` attribute is not always available; in that
    case we fall back to the current RSS as a best‑effort estimate.

    Returns
    -------
    float
        Peak memory usage in MB.
    """
    mem_info = _process().memory_info()
    # ``peak_wset`` is Windows‑specific; ``uss`` (Unique Set Size) is a
    # reasonable cross‑platform alternative on recent psutil versions.
    peak_bytes = getattr(mem_info, "peak_wset", None) or getattr(
        mem_info, "uss", None
    ) or mem_info.rss
    peak_mb = peak_bytes / (1024 ** 2)
    _logger.debug("Peak memory usage: %.2f MB", peak_mb)
    return peak_mb


def memory_profile(func: T) -> T:
    """
    Decorator that logs memory usage before and after the wrapped function
    call.  The decorator returns the original function's result unchanged.

    Example
    -------
    >>> @memory_profile
    ... def heavy_computation():
    ...     # ... do work ...
    ...     return result
    >>> heavy_computation()
    # Logs something like:
    #   INFO utils – Memory before heavy_computation: 123.45 MB
    #   INFO utils – Memory after heavy_computation: 456.78 MB

    Parameters
    ----------
    func : Callable
        The function to wrap.

    Returns
    -------
    Callable
        Wrapped function with the same signature as ``func``.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:  # type: ignore[misc]
        mem_before = get_current_memory_mb()
        _logger.info(
            "Memory before %s: %.2f MB", func.__name__, mem_before
        )
        result = func(*args, **kwargs)
        mem_after = get_current_memory_mb()
        _logger.info(
            "Memory after %s: %.2f MB", func.__name__, mem_after
        )
        return result

    return cast(T, wrapper)