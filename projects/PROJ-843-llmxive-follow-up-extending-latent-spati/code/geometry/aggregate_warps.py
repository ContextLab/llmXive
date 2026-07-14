"""
Utilities to aggregate per‑sequence warped frames produced by the
geometry pipeline.

The original implementation only returned the aggregated array in memory.
This version ensures that the aggregated result is persisted to
``data/results/sparse_warped_frames.npy`` – the canonical artifact
required by downstream evaluation scripts.
"""

import json
import os
from pathlib import Path
from typing import List

import numpy as np

from config import (
    get_features_dir,
    get_results_dir,
    ensure_directories,
)

# ----------------------------------------------------------------------
def scan_warped_frames() -> List[Path]:
    """
    Return a list of all ``.npy`` files inside the features directory that
    represent warped frames.
    """
    features_dir = get_features_dir()
    return sorted([p for p in features_dir.rglob("*.npy") if p.is_file()])

# ----------------------------------------------------------------------
def load_warped_frame(path: Path) -> np.ndarray:
    """Load a single warped frame from ``path``."""
    return np.load(path, allow_pickle=False)

# ----------------------------------------------------------------------
def validate_aggregated_data(arr: np.ndarray) -> None:
    """
    Basic sanity check: ensure the aggregated array has at least one frame
    and that the dtype is ``uint8`` (standard image representation).
    """
    if arr.size == 0:
        raise ValueError("Aggregated warped frames array is empty.")
    if arr.dtype != np.uint8:
        raise ValueError(f"Unexpected dtype {arr.dtype}; expected uint8.")

# ----------------------------------------------------------------------
def aggregate_warped_frames() -> np.ndarray:
    """
    Load all warped frame ``.npy`` files, concatenate them along the first
    dimension, validate the result and return it.
    """
    paths = scan_warped_frames()
    if not paths:
        raise FileNotFoundError("No warped frame files found in features directory.")
    frames = [load_warped_frame(p) for p in paths]
    aggregated = np.concatenate(frames, axis=0)
    validate_aggregated_data(aggregated)
    return aggregated

# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry‑point used by the quick‑start run‑book.  It aggregates the warped
    frames and writes the result to ``data/results/sparse_warped_frames.npy``.
    """
    ensure_directories()
    aggregated = aggregate_warped_frames()
    output_path = get_results_dir() / "sparse_warped_frames.npy"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, aggregated)
    print(f"Aggregated warped frames saved to {output_path}")

if __name__ == "__main__":  # pragma: no cover
    main()
