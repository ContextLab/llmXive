"""Utility module for resource guard checks.

This module computes the total size of the ``data/raw`` directory and
determines whether the pipeline should run in ``full`` mode or switch to
``streaming`` mode when the raw data exceeds the 7 GB RAM limit.

The chosen mode is written to ``outputs/logs/guard_log.txt`` with a line
of the form ``resource_guard: mode=<mode>``.  Down‑stream scripts can read
this file to adjust their loading strategy.
"""
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Path to the raw data directory and to the guard‑log file.
RAW_DATA_PATH = paths.data("raw")
GUARD_LOG_PATH = paths.outputs("logs", "guard_log.txt")

# ----------------------------------------------------------------------
# Internal helper to compute the total size of all files under ``data/raw``.
# ----------------------------------------------------------------------
def _compute_raw_data_size_bytes() -> int:
    """Return the total size in bytes of all files in ``data/raw``."""
    total = 0
    if RAW_DATA_PATH.exists():
        for p in RAW_DATA_PATH.rglob("*"):
            if p.is_file():
                total += p.stat().st_size
    return total

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def get_resource_mode() -> str:
    """Determine the resource‑guard mode.

    Returns
    -------
    str
        ``"streaming"`` if the raw data size exceeds 7 GB, otherwise
        ``"full"``.
    """
    size_bytes = _compute_raw_data_size_bytes()
    threshold_bytes = 7 * 1024 ** 3  # 7 GB
    mode = "streaming" if size_bytes > threshold_bytes else "full"

    # Ensure the log directory exists and write the mode.
    GUARD_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    GUARD_LOG_PATH.write_text(f"resource_guard: mode={mode}\n")

    log.info(
        "resource_guard: mode=%s (raw data size=%d bytes)", mode, size_bytes
    )
    return mode

# Perform the check on import so that the log file is created early.
_RESOURCE_MODE = get_resource_mode()
