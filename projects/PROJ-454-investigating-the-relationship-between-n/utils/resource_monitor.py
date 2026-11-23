"""
utils/resource_monitor.py

Resource monitoring utilities for the Neural Entropy project.

This module provides functions to:
  * Record the current RAM and disk usage.
  * Abort execution if usage exceeds the limits defined in the
    specification (7 GB RAM, 14 GB disk).
  * Offer a simple context‑manager API (`record`) that can be used at
    the start and end of any pipeline script.

The module is deliberately lightweight and only depends on the
standard library plus ``psutil`` (added to ``requirements.txt``).  All
paths are resolved relative to the project root (the directory that
contains the top‑level ``logs/`` folder).

Usage example (typical in a pipeline script)::

    from utils.resource_monitor import record, check_resource_limits, log_resource_snapshot

    # Record a snapshot at script start
    log_resource_snapshot("script start")
    check_resource_limits()   # abort if limits already exceeded

    # ... pipeline code ...

    # Record a snapshot at script end
    log_resource_snapshot("script end")
    check_resource_limits()   # final safety check

Or, using the context manager::

    from utils.resource_monitor import ResourceMonitor

    with ResourceMonitor(stage="02_preprocess_eeg"):
        # pipeline code here
        ...

The verification step for T004 simply checks that a line appears in
``logs/resource_usage.log`` during script execution, so each call to
``log_resource_snapshot`` writes a timestamped entry.
"""

import os
import sys
import json
import datetime
import shutil
from pathlib import Path
from typing import Optional

# ``psutil`` is listed in ``requirements.txt``.  Import lazily so that a
# missing dependency raises a clear error at runtime (the execution
# environment will install it before any script runs).
try:
    import psutil
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "psutil is required for utils.resource_monitor. "
        "Please ensure it is listed in requirements.txt and installed."
    ) from exc

# ----------------------------------------------------------------------
# Configuration – limits from the specification (FR‑008)
# ----------------------------------------------------------------------
_RAM_LIMIT_GB = 7.0          # Maximum RAM usage before aborting
_DISK_LIMIT_GB = 14.0        # Maximum disk usage (project root) before aborting

# Resolve the project root (the directory that contains the top‑level
# ``logs`` folder).  ``utils`` lives in ``code/utils``; two ``parent``
# hops bring us to the repository root.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Ensure the ``logs`` directory exists early – many scripts import this
# module before any logging infrastructure is set up.
_LOG_DIR = _PROJECT_ROOT / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_LOG_FILE = _LOG_DIR / "resource_usage.log"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _timestamp() -> str:
    """Return an ISO‑8601 timestamp."""
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _format_size_gb(bytes_: int) -> float:
    """Convert a size in bytes to gigabytes (rounded to two decimals)."""
    return round(bytes_ / (1024.0 ** 3), 2)

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def get_memory_usage_gb() -> float:
    """
    Return the resident set size (RSS) of the current Python process in GB.

    The measurement is taken from ``psutil.Process(os.getpid()).memory_info()``.
    """
    process = psutil.Process(os.getpid())
    rss_bytes = process.memory_info().rss
    return _format_size_gb(rss_bytes)

def get_disk_usage_gb() -> float:
    """
    Return the *used* disk space of the project root in GB.

    ``shutil.disk_usage`` reports the total, used and free bytes on the
    filesystem that contains ``_PROJECT_ROOT``.  Only the *used* portion
    is relevant for the specification's “>14 GB disk” rule.
    """
    usage = shutil.disk_usage(_PROJECT_ROOT)
    return _format_size_gb(usage.used)

def log_resource_snapshot(message: Optional[str] = None) -> None:
    """
    Write a single line to ``logs/resource_usage.log`` containing:

        <timestamp> | RAM: <value> GB | Disk: <value> GB | <optional message>

    The function is deliberately side‑effect‑only; it never raises.
    """
    timestamp = _timestamp()
    ram_gb = get_memory_usage_gb()
    disk_gb = get_disk_usage_gb()
    parts = [timestamp, f"RAM: {ram_gb} GB", f"Disk: {disk_gb} GB"]
    if message:
        parts.append(message)
    line = " | ".join(parts)

    # Append atomically; ``open(..., 'a')`` is safe for concurrent writes
    # because the CI runner executes scripts sequentially.
    with _LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def check_resource_limits() -> None:
    """
    Abort execution if the current RAM or disk usage exceeds the limits.

    The function logs a descriptive line to the resource‑usage log before
    raising ``SystemExit``.  Raising ``SystemExit`` is the cleanest way to
    abort a script without leaking a traceback to the user (the CI runner
    will treat a non‑zero exit code as a failure).
    """
    ram = get_memory_usage_gb()
    disk = get_disk_usage_gb()
    exceeded = []

    if ram > _RAM_LIMIT_GB:
        exceeded.append(f"RAM {ram:.2f} GB > {_RAM_LIMIT_GB} GB")
    if disk > _DISK_LIMIT_GB:
        exceeded.append(f"Disk {disk:.2f} GB > {_DISK_LIMIT_GB} GB")

    if exceeded:
        message = "RESOURCE LIMIT EXCEEDED: " + "; ".join(exceeded)
        log_resource_snapshot(message)
        # ``SystemExit`` with a non‑zero code signals failure to the CI runner.
        sys.exit(1)

class ResourceMonitor:
    """
    Context manager that records RAM/Disk usage on entry and exit.

    Example
    -------
    >>> from utils.resource_monitor import ResourceMonitor
    >>> with ResourceMonitor(stage="02_preprocess_eeg"):
    ...     # pipeline code here
    ...     pass
    """

    def __init__(self, stage: str = "unknown"):
        self.stage = stage

    def __enter__(self):
        log_resource_snapshot(f"START stage={self.stage}")
        # Immediate check – if the environment is already over the limit we
        # abort before any heavy work begins.
        check_resource_limits()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Record a final snapshot regardless of success/failure.
        log_resource_snapshot(f"END stage={self.stage}")
        # Perform a final safety check; if limits are exceeded we still
        # abort (the exit code will be non‑zero).
        check_resource_limits()
        # Propagate any exception (do not suppress).
        return False

# ----------------------------------------------------------------------
# Backwards‑compatible convenience wrappers
# ----------------------------------------------------------------------
def record(message: Optional[str] = None) -> None:
    """
    Backwards‑compatible alias used by older scripts.

    It simply forwards to ``log_resource_snapshot``.  Keeping this thin
    wrapper avoids having to touch many existing imports.
    """
    log_resource_snapshot(message)
