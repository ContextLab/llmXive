"""
Utility functions for loading large fMRI NIfTI files in a memory‑efficient,
chunked manner.

The primary entry point is :func:`load_chunked_fMRI` which yields NumPy
arrays of shape ``(X, Y, Z, T_chunk)`` without ever loading the full
4‑D volume into memory.  This is useful when the time dimension is large
(e.g. several thousand volumes) and the available RAM is limited (the
project caps RAM at 7 GB).

The implementation relies on ``nibabel``'s lazy ``dataobj`` interface,
which supports NumPy‑style slicing without reading the whole file.
Chunk size is automatically determined from the configured RAM budget
(``config.max_ram_gb``) but can be overridden by the caller.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Generator, Iterable, Tuple, Union

import numpy as np
import nibabel as nib
import psutil

# Project configuration – we reuse the constants defined in ``code/config.py``.
try:
    from config import max_ram_gb as DEFAULT_MAX_RAM_GB
except Exception:  # pragma: no cover
    # Fallback in case the config module is not importable (e.g. during isolated tests)
    DEFAULT_MAX_RAM_GB = 7

__all__ = ["load_chunked_fMRI", "estimate_chunk_size"]


def _available_ram_gb() -> float:
    """Return the amount of *available* RAM in gigabytes."""
    mem = psutil.virtual_memory()
    # Use only the free portion; reserve a safety margin.
    free_gb = mem.available / (1024**3)
    return free_gb


def estimate_chunk_size(
    img_shape: Tuple[int, int, int, int],
    max_ram_gb: Union[float, None] = None,
    safety_factor: float = 0.5,
) -> int:
    """
    Compute a safe number of timepoints to load per chunk.

    Parameters
    ----------
    img_shape : Tuple[int, int, int, int]
        The full 4‑D shape of the NIfTI image (X, Y, Z, T).
    max_ram_gb : float or None
        Upper bound on RAM usage for the chunk (in GB).  If ``None``,
        the project's ``max_ram_gb`` configuration is used.
    safety_factor : float, default 0.5
        Fraction of the RAM budget to actually allocate for the data
        (the rest is kept free for Python overhead, other objects, etc.).

    Returns
    -------
    int
        Number of timepoints that can be safely loaded at once.
    """
    if max_ram_gb is None:
        max_ram_gb = DEFAULT_MAX_RAM_GB

    # Ensure we do not request more RAM than the system currently has.
    max_ram_gb = min(max_ram_gb, _available_ram_gb())

    # Number of spatial voxels
    voxels = img_shape[0] * img_shape[1] * img_shape[2]
    if voxels == 0:
        raise ValueError("Image has zero voxels in spatial dimensions.")

    # Memory needed for one timepoint (float32 -> 4 bytes)
    bytes_per_tp = voxels * 4
    # Convert GB to bytes and apply safety factor
    max_bytes = max_ram_gb * (1024**3) * safety_factor

    # At least one timepoint per chunk
    chunk_tp = max(int(max_bytes // bytes_per_tp), 1)

    # Do not exceed the total number of timepoints
    chunk_tp = min(chunk_tp, img_shape[3])
    return chunk_tp


def load_chunked_fMRI(
    file_path: Union[str, Path],
    chunk_size: Union[int, None] = None,
    max_ram_gb: Union[float, None] = None,
) -> Generator[np.ndarray, None, None]:
    """
    Yield successive chunks of a 4‑D NIfTI fMRI file.

    The function streams the data along the time axis (the 4th dimension)
    and never holds the entire volume in memory.

    Parameters
    ----------
    file_path : str or pathlib.Path
        Path to the NIfTI (``.nii`` or ``.nii.gz``) file.
    chunk_size : int or None, optional
        Desired number of timepoints per chunk.  If ``None`` the size is
        automatically estimated from the RAM budget.
    max_ram_gb : float or None, optional
        Upper bound on RAM usage for a chunk (in GB).  Ignored if
        ``chunk_size`` is provided.

    Yields
    ------
    numpy.ndarray
        A 4‑D array with shape ``(X, Y, Z, T_chunk)`` of type ``float32``.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"fMRI file not found: {path}")

    # Load header lazily – ``dataobj`` provides on‑demand slicing.
    img = nib.load(str(path))
    dataobj = img.dataobj  # type: ignore[attr-defined]

    # Ensure we have a 4‑D image.
    if len(dataobj.shape) != 4:
        raise ValueError(f"Expected a 4‑D fMRI image, got shape {dataobj.shape}")

    x, y, z, t_total = dataobj.shape

    if chunk_size is None:
        chunk_size = estimate_chunk_size(
            img_shape=dataobj.shape, max_ram_gb=max_ram_gb
        )

    # Iterate over the time dimension.
    for start in range(0, t_total, chunk_size):
        end = min(start + chunk_size, t_total)
        # Slice lazily; ``np.asarray`` forces materialisation of the chunk only.
        chunk = np.asarray(dataobj[..., start:end], dtype=np.float32)
        yield chunk

# ----------------------------------------------------------------------
# Simple command‑line demo (not used by the pipeline but handy for manual testing)
# ----------------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover
    if len(sys.argv) != 2:
        print("Usage: python -m utils.loaders <path-to-nifti>")
        sys.exit(1)

    fp = Path(sys.argv[1])
    print(f"Streaming '{fp}' …")
    for i, ch in enumerate(load_chunked_fMRI(fp)):
        print(f"Chunk {i + 1}: shape {ch.shape}, dtype {ch.dtype}")
    print("Done.")
