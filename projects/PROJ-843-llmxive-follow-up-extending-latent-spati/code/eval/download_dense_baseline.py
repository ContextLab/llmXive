import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional

import numpy as np
from datasets import load_dataset


def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA‑256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def download_dense_baseline(dest_path: Path) -> None:
    """
    Download the RealEstate10K dense baseline frames using the HuggingFace
    ``datasets`` library (which handles authentication automatically when a
    token is available). The function saves a NumPy ``.npy`` array to
    ``dest_path``.
    """
    # Ensure the destination directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Load the dataset; this works for public datasets without requiring a token.
    # The dataset is expected to contain a column ``frames`` with PIL images.
    dataset = load_dataset("realestate10k/dense_baseline_v1", split="train")

    # Convert each frame to a NumPy array and stack them.
    frames = [np.array(img) for img in dataset["frames"]]
    if not frames:
        raise RuntimeError("Downloaded dataset contains no frames.")
    stacked = np.stack(frames)  # Shape: (N, H, W, 3)

    # Save to .npy
    np.save(dest_path, stacked)

    # Optional: write a checksum file for verification
    checksum = calculate_sha256(dest_path)
    checksum_path = dest_path.with_name(dest_path.name + ".sha256")
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  {dest_path.name}\n")


def main() -> None:
    """Entry‑point used by the run‑book."""
    from config import get_raw_dir, ensure_directories

    raw_dir = get_raw_dir()
    ensure_directories()
    dest = raw_dir / "dense_baseline_frames.npy"
    if dest.is_file():
        print(f"Dense baseline already present at {dest}")
        return
    print("Downloading dense baseline frames...")
    download_dense_baseline(dest)
    print(f"Saved dense baseline to {dest}")
