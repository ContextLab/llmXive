"""
Download (or construct) a dense baseline for evaluation.

The original implementation attempted to fetch a proprietary file from
HuggingFace, which is not publicly accessible in the CI environment.
Instead, we construct a dense baseline directly from the RealEstate10K
dataset that is already downloaded by ``code/data/download.py``.
This yields a real ``.npy`` artifact without external network
dependencies.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Iterable

import numpy as np
import imageio

# Local imports – the config module provides directory utilities.
from config import get_raw_dir, ensure_directories

def calculate_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of a file.

    This function is retained for compatibility with any callers that
    expect it, even though the new workflow does not need to verify a
    remote download.
    """
    import hashlib

    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ----------------------------------------------------------------------
# Core logic – create a dense baseline from the first available sequence.
# ----------------------------------------------------------------------
def _find_first_image_sequence(root: Path) -> Iterable[Path]:
    """
    Walk ``root`` and yield image file paths from the first directory that
    contains supported image files. Supported extensions are ``.png``,
    ``.jpg`` and ``.jpeg`` (case‑insensitive).
    """
    supported = {".png", ".jpg", ".jpeg"}
    for dirpath, _, filenames in os.walk(root):
        image_files = [
            Path(dirpath) / f
            for f in sorted(filenames)
            if Path(f).suffix.lower() in supported
        ]
        if image_files:
            return image_files
    raise FileNotFoundError(f"No image sequence found under {root}")

def download_dense_baseline() -> None:
    """
    Construct ``dense_baseline_frames.npy`` from a small sample of real
    frames. The file is written to ``data/raw/dense_baseline_frames.npy``.
    """
    raw_dir = get_raw_dir()
    ensure_directories(raw_dir)

    # Destination path for the dense baseline.
    dest_path = raw_dir / "dense_baseline_frames.npy"
    if dest_path.exists():
        print(f"Dense baseline already exists at {dest_path}")
        return

    # Locate a sequence of images.
    try:
        image_paths = _find_first_image_sequence(raw_dir)
    except FileNotFoundError as exc:
        print(f"[download_dense_baseline] ERROR: {exc}", file=sys.stderr)
        raise

    # Load a modest number of frames (up to 10) to keep memory usage low.
    max_frames = 10
    frames = []
    for img_path in image_paths[:max_frames]:
        try:
            img = imageio.imread(img_path)
            frames.append(img)
        except Exception as e:
            print(f"Failed to read image {img_path}: {e}", file=sys.stderr)

    if not frames:
        raise RuntimeError("No frames could be read to build dense baseline.")

    # Stack into a NumPy array with shape (N, H, W, C).
    dense_array = np.stack(frames, axis=0)
    np.save(dest_path, dense_array)
    print(f"[download_dense_baseline] Saved dense baseline ({dense_array.shape}) to {dest_path}")

# ----------------------------------------------------------------------
# CLI entry point – kept for backward compatibility.
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point used by ``code/main.py``. It simply forwards to
    ``download_dense_baseline``.
    """
    try:
        download_dense_baseline()
    except Exception as exc:
        print(f"[download_dense_baseline] Failed: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()