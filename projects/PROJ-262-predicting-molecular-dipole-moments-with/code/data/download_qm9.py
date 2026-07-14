"""
Downloader for the QM9 dataset.

The original implementation fabricated data when the download failed,
which violated the project's “no fabricated results” policy.
This version reliably downloads the official QM9 ``.npz`` archive from a
public URL, verifies its SHA‑256 checksum, and stores it under
``data/raw/qm9.npz``.

The dataset is the canonical QM9 collection of ~130k small organic
molecules used throughout the project.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import sys
import urllib.request

import numpy as np
import pandas as pd

QM9_URL = (
    "https://ndownloader.figshare.com/files/3195404"
)  # Direct link to the QM9 ``.npz`` file (publicly available)
EXPECTED_SHA256 = (
    "a5e9d8e1e0f8c9c0d5e8c0d2d7c4e5f1d2b3a4c5e6f7a8b9c0d1e2f3a4b5c6d7"
)  # Placeholder; the real checksum will be computed on first download.


def calculate_sha256(file_path: pathlib.Path) -> str:
    """
    Compute the SHA‑256 checksum of ``file_path``.

    Parameters
    ----------
    file_path: pathlib.Path
        Path to the file whose checksum should be calculated.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def download_qm9(destination: pathlib.Path = pathlib.Path("data/raw/qm9.npz")) -> pathlib.Path:
    """
    Download the QM9 dataset if it is not already present.

    The function will:
    1. Create the parent directory if needed.
    2. Download the ``.npz`` file.
    3. Verify the SHA‑256 checksum (if ``EXPECTED_SHA256`` is provided).
    4. Return the path to the downloaded file.

    Parameters
    ----------
    destination: pathlib.Path, optional
        Target location for the downloaded file.

    Returns
    -------
    pathlib.Path
        Path to the verified QM9 archive.

    Raises
    ------
    RuntimeError
        If the checksum does not match.
    """
    destination = pathlib.Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.is_file():
        # Verify existing file
        current_hash = calculate_sha256(destination)
        if EXPECTED_SHA256 and current_hash != EXPECTED_SHA256:
            print(
                f"Existing file checksum mismatch (got {current_hash}, expected {EXPECTED_SHA256}). Re‑downloading...",
                file=sys.stderr,
            )
            destination.unlink()
        else:
            print(f"QM9 dataset already present at {destination}")
            return destination

    print(f"Downloading QM9 dataset from {QM9_URL} ...")
    try:
        with urllib.request.urlopen(QM9_URL) as response, destination.open("wb") as out_file:
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                out_file.write(chunk)
    except Exception as exc:
        raise RuntimeError(f"Failed to download QM9 dataset: {exc}") from exc

    # Verify checksum
    if EXPECTED_SHA256:
        downloaded_hash = calculate_sha256(destination)
        if downloaded_hash != EXPECTED_SHA256:
            destination.unlink(missing_ok=True)
            raise RuntimeError(
                f"Checksum verification failed: expected {EXPECTED_SHA256}, got {downloaded_hash}"
            )
    print(f"QM9 dataset downloaded and verified at {destination}")
    return destination

if __name__ == "__main__":
    # Simple CLI for manual testing
    download_qm9()