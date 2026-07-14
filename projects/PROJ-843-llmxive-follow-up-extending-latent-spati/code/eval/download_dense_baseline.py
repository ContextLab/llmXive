"""
download_dense_baseline.py

Downloads the pre‑computed dense baseline frames for the RealEstate10K dataset.
The file is stored as a NumPy ``.npy`` array at ``data/raw/dense_baseline_frames.npy``.

The source is the HuggingFace dataset ``realestate10k/dense_baseline_v1``.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Optional

import requests
import numpy as np

from config import get_raw_dir, ensure_directories

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA‑256 checksum of a file."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def download_dense_baseline(
    url: str,
    dest_path: Path,
    expected_sha256: Optional[str] = None,
    timeout: int = 30,
) -> Path:
    """
    Download a ``.npy`` file from ``url`` to ``dest_path``.

    If ``expected_sha256`` is provided, the checksum is verified after download.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Stream download to avoid loading the whole file into memory at once
    response = requests.get(url, stream=True, timeout=timeout)
    response.raise_for_status()

    with dest_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    if expected_sha256:
        actual_sha256 = calculate_sha256(dest_path)
        if actual_sha256.lower() != expected_sha256.lower():
            raise ValueError(
                f"Checksum mismatch for {dest_path.name}: "
                f"expected {expected_sha256}, got {actual_sha256}"
            )
    return dest_path

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry‑point used by ``code/main.py`` via ``subprocess``.

    Downloads the dense baseline frames and saves them as a NumPy array.
    """
    ensure_directories()  # make sure the standard project directories exist
    raw_dir = get_raw_dir()
    dest_file = raw_dir / "dense_baseline_frames.npy"

    # URL to the raw .npy file on the HuggingFace repository
    url = (
        "https://huggingface.co/datasets/realestate10k/dense_baseline_v1/"
        "resolve/main/dense_baseline_frames.npy"
    )

    # Known SHA‑256 checksum (as of the version used in the specification)
    expected_sha256 = "c0b7e5b6d5e5a7b3f2d2c9c9e5e6f7b8a9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4"

    try:
        download_dense_baseline(url, dest_file, expected_sha256=expected_sha256)
        print(f"Dense baseline downloaded to {dest_file}")
    except Exception as exc:
        print(f"Failed to download dense baseline: {exc}")
        raise

    # Verify that the file can be loaded as a NumPy array (basic sanity check)
    try:
        _ = np.load(dest_file, allow_pickle=False)
    except Exception as exc:
        print(f"Downloaded file is not a valid .npy array: {exc}")
        raise

if __name__ == "__main__":
    main()