"""
Utilities for aggregating warped frame results.

Public API:
  * ``scan_warped_frames`` – locate all ``*.npy`` files in the results dir.
  * ``load_warped_frame`` – load a single warped frame array.
  * ``validate_aggregated_data`` – sanity‑check the collected frames.
  * ``aggregate_warped_frames`` – stack frames and write the consolidated file.
  * ``main`` – entry‑point used by the geometry pipeline.
"""

import json
import os
from pathlib import Path
from typing import List
import numpy as np

from config import get_results_dir, ensure_directories

# ----------------------------------------------------------------------
def _ensure_path(p: Union[str, Path]) -> Path:
    """Utility to coerce ``str`` or ``Path`` to a ``Path`` instance."""
    return p if isinstance(p, Path) else Path(p)

# ----------------------------------------------------------------------
def scan_warped_frames(results_dir: Union[str, Path]) -> List[Path]:
    """
    Return a list of all ``*.npy`` files inside ``results_dir``.
    """
    results_path = _ensure_path(results_dir)
    return sorted(results_path.glob("*.npy"))

# ----------------------------------------------------------------------
def load_warped_frame(npy_path: Union[str, Path]) -> np.ndarray:
    """
    Load a single warped frame stored as a NumPy ``.npy`` file.
    """
    path = _ensure_path(npy_path)
    return np.load(path)

# ----------------------------------------------------------------------
def validate_aggregated_data(frames: List[np.ndarray]) -> None:
    """
    Basic validation – raises ``ValueError`` if the list is empty or if any
    frame has an unexpected shape.
    """
    if not frames:
        raise ValueError("No warped frames found to aggregate.")
    # Ensure all frames share the same shape.
    first_shape = frames[0].shape
    for i, arr in enumerate(frames):
        if arr.shape != first_shape:
            raise ValueError(
                f"Frame {i} shape {arr.shape} differs from expected {first_shape}"
            )

# ----------------------------------------------------------------------
def aggregate_warped_frames() -> None:
    """
    Load all warped ``.npy`` files from the results directory, validate
    them, and write a single stacked array to
    ``data/results/sparse_warped_frames.npy``.
    """
    results_dir = get_results_dir()
    ensure_directories(results_dir)

    warped_paths = scan_warped_frames(results_dir)
    frames = [load_warped_frame(p) for p in warped_paths]

    validate_aggregated_data(frames)

    # Stack along a new first axis (frame index).
    aggregated = np.stack(frames, axis=0)

    out_path = results_dir / "sparse_warped_frames.npy"
    np.save(out_path, aggregated)
    print(f"[aggregate_warps] Aggregated {len(frames)} frames → {out_path}")

# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry‑point used by ``code/geometry/run_pipeline.py``.
    """
    aggregate_warped_frames()