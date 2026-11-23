"""
utils.py

Helper utilities for resource‑guarding and mode selection.
"""

from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _compute_raw_data_size_bytes() -> int:
    """
    Return the total size in bytes of all files in ``data/raw``.
    """
    raw_dir = paths.data("raw")
    total = 0
    for p in raw_dir.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total

def get_resource_mode() -> str:
    """
    Determine the resource‑guard mode.

    Returns
    -------
    str
        ``"streaming"`` if the raw data size exceeds 7 GB, otherwise
        ``"full"``.
    """
    size_bytes = _compute_raw_data_size_bytes()
    size_gb = size_bytes / (1024 ** 3)
    mode = "streaming" if size_gb > 7 else "full"
    log.info(f"resource_guard: mode={mode} (size={size_gb:.2f} GB)")
    return mode