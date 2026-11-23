"""
src/metrics/load_stimuli.py

Implements loading of previously fetched and archived visual background stimuli.
The archive is expected to reside under ``data/stimuli/raw/`` and contain a
``manifest.json`` file mapping each image filename to its SHA‑256 checksum.
This module verifies the integrity of each file, loads the image as a NumPy
array and returns a list of loaded stimuli.

Public API
----------
* ``StimuliLoaderError`` – custom exception for loader failures.
* ``load_stimuli_from_archive(max_images: int | None = None)`` – loads and
  returns a list of ``(filename, image_array)`` tuples.
* ``get_stimuli_metadata()`` – reads and returns the manifest dictionary.
* ``main()`` – CLI entry point for manual execution / debugging.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
from PIL import Image

# Local utilities
from src.lib.utils import compute_file_checksum

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

# Project root is two levels up from this file (src/metrics/ -> src/ -> project root)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_RAW_STIMULI_DIR = _PROJECT_ROOT / "data" / "stimuli" / "raw"
_MANIFEST_PATH = _RAW_STIMULI_DIR / "manifest.json"

# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #

class StimuliLoaderError(Exception):
    """Raised for any problem encountered while loading the stimuli archive."""
    pass

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def get_stimuli_metadata() -> Dict[str, str]:
    """
    Load the manifest that maps image filenames to their expected SHA‑256 checksums.

    Returns
    -------
    dict
        ``{filename: checksum}`` mapping.

    Raises
    ------
    StimuliLoaderError
        If the manifest file does not exist or cannot be parsed.
    """
    if not _MANIFEST_PATH.is_file():
        raise StimuliLoaderError(
            f"Manifest file not found at expected location: {_MANIFEST_PATH}"
        )
    try:
        with _MANIFEST_PATH.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as exc:
        raise StimuliLoaderError(f"Failed to read manifest JSON: {exc}") from exc

    if not isinstance(manifest, dict):
        raise StimuliLoaderError("Manifest JSON must be an object mapping filenames to checksums.")
    return manifest

def _verify_checksum(file_path: Path, expected_checksum: str) -> None:
    """
    Compute the SHA‑256 checksum of ``file_path`` and compare it to ``expected_checksum``.

    Raises
    ------
    StimuliLoaderError
        If the computed checksum differs from the expected value.
    """
    actual = compute_file_checksum(file_path)
    if actual.lower() != expected_checksum.lower():
        raise StimuliLoaderError(
            f"Checksum mismatch for {file_path.name}: expected {expected_checksum}, got {actual}"
        )

def _load_image(file_path: Path) -> np.ndarray:
    """
    Load an image file using Pillow and return it as a NumPy ``uint8`` array
    with shape ``(H, W, 3)`` in RGB order.

    Raises
    ------
    StimuliLoaderError
        If Pillow cannot open or decode the image.
    """
    try:
        with Image.open(file_path) as img:
            img = img.convert("RGB")
            return np.array(img, dtype=np.uint8)
    except Exception as exc:
        raise StimuliLoaderError(f"Failed to load image {file_path.name}: {exc}") from exc

# --------------------------------------------------------------------------- #
# Public loader
# --------------------------------------------------------------------------- #

def load_stimuli_from_archive(max_images: Optional[int] = None) -> List[Tuple[str, np.ndarray]]:
    """
    Load stimuli images from the local archive, verifying checksums.

    Parameters
    ----------
    max_images : int | None
        If provided, load at most this many images (useful for quick tests).

    Returns
    -------
    list[tuple[str, np.ndarray]]
        A list where each element is ``(filename, image_array)``.

    Raises
    ------
    StimuliLoaderError
        If the archive directory, manifest, or any file fails verification.
    """
    if not _RAW_STIMULI_DIR.is_dir():
        raise StimuliLoaderError(
            f"Stimuli archive directory does not exist: {_RAW_STIMULI_DIR}"
        )

    manifest = get_stimuli_metadata()
    loaded: List[Tuple[str, np.ndarray]] = []

    # Preserve deterministic order for reproducibility
    sorted_filenames = sorted(manifest.keys())

    for idx, filename in enumerate(sorted_filenames):
        if max_images is not None and idx >= max_images:
            break

        file_path = _RAW_STIMULI_DIR / filename
        if not file_path.is_file():
            raise StimuliLoaderError(f"Expected image file missing: {file_path}")

        expected_checksum = manifest[filename]
        _verify_checksum(file_path, expected_checksum)

        image_array = _load_image(file_path)
        loaded.append((filename, image_array))

    return loaded

# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load verified stimuli from the local archive."
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help="Maximum number of images to load (default: load all).",
    )
    return parser

def main() -> None:
    """
    Simple command‑line interface that loads the stimuli and prints a short
    summary. This is primarily for manual debugging; the production pipeline
    will import ``load_stimuli_from_archive`` directly.
    """
    args = _build_arg_parser().parse_args()
    stimuli = load_stimuli_from_archive(max_images=args.max_images)

    print(f"Loaded {len(stimuli)} stimulus image(s) from {_RAW_STIMULI_DIR}")
    for fname, img in stimuli[:5]:  # show first few as a sanity check
        print(f" - {fname}: shape={img.shape}, dtype={img.dtype}")

if __name__ == "__main__":
    main()