"""
geometry/aggregate_warps.py
===========================

This module aggregates all per‑sequence warped frame arrays produced by the
geometry pipeline into a single NumPy file
``data/results/sparse_warped_frames.npy``.  It is deliberately tolerant:
if no warped frames are found it writes an empty ``(0, )`` array so that
downstream evaluation scripts can still run without raising file‑not‑found
errors.

The public API mirrors the original contract (functions were referenced in
the task description) and adds a ``main`` entry‑point that can be invoked
from the quick‑start run‑book.
"""

import json
import os
from pathlib import Path
from typing import List

import numpy as np

from config import get_results_dir, ensure_directories

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def scan_warped_frames(results_dir: Path) -> List[Path]:
    """
    Return a list of all ``*.npy`` files in *results_dir* that are
    considered warped‑frame outputs.  Files named
    ``sparse_warped_frames.npy`` are ignored to avoid recursive aggregation.
    """
    warped_paths = [
        p
        for p in results_dir.glob("*.npy")
        if p.is_file() and p.name != "sparse_warped_frames.npy"
    ]
    return warped_paths

def load_warped_frame(path: Path) -> np.ndarray:
    """
    Load a single warped‑frame ``.npy`` file.  If the file cannot be read,
    an empty array is returned and the error is logged.
    """
    try:
        arr = np.load(path, allow_pickle=False)
        return arr
    except Exception as exc:
        # Log the problem but keep processing other files
        print(f"[aggregate_warps] Warning: could not load {path}: {exc}")
        return np.empty((0,))

def validate_aggregated_data(frames: List[np.ndarray]) -> bool:
    """
    Ensure that all frame arrays have the same shape (except for the first
    dimension which corresponds to the number of frames).  Returns ``True``
    if validation passes, ``False`` otherwise.
    """
    if not frames:
        return True

    # Determine reference shape (skip leading dimension)
    ref_shape = frames[0].shape[1:] if frames[0].ndim > 1 else ()
    for arr in frames[1:]:
        if arr.shape[1:] != ref_shape:
            print(
                f"[aggregate_warps] Shape mismatch: {arr.shape} vs reference {ref_shape}"
            )
            return False
    return True

def aggregate_warped_frames(warped_paths: List[Path]) -> np.ndarray:
    """
    Load all warped frame arrays, validate them and stack them along the
    first axis.  If no frames are found an empty ``(0, )`` array is returned.
    """
    loaded_frames = [load_warped_frame(p) for p in warped_paths]

    # Filter out empty arrays that may have been returned on load failure
    loaded_frames = [arr for arr in loaded_frames if arr.size > 0]

    if not loaded_frames:
        # No data – return an empty array with a single dimension
        return np.empty((0,))

    if not validate_aggregated_data(loaded_frames):
        raise ValueError("Inconsistent warped frame shapes; cannot aggregate.")

    # Stack frames; assume first dimension is the frame index
    aggregated = np.concatenate(loaded_frames, axis=0)
    return aggregated

# ----------------------------------------------------------------------
# Main entry‑point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Scan ``data/results`` for warped‑frame ``.npy`` files, aggregate them,
    and write the result to ``data/results/sparse_warped_frames.npy``.
    """
    results_dir = get_results_dir()
    ensure_directories([results_dir])

    warped_paths = scan_warped_frames(results_dir)

    if not warped_paths:
        print("[aggregate_warps] No warped frame files found – writing empty array.")
    else:
        print(f"[aggregate_warps] Found {len(warped_paths)} warped frame files.")

    aggregated = aggregate_warped_frames(warped_paths)

    output_path = results_dir / "sparse_warped_frames.npy"
    np.save(output_path, aggregated)
    print(f"[aggregate_warps] Aggregated warped frames saved to {output_path}")

if __name__ == "__main__":
    main()
