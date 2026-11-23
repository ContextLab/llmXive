"""
Download GLUE SST-2 dataset for the dendritic computation experiments.

This script fetches the real SST-2 files directly from the HuggingFace hub,
stores them under `data/raw/sst2/`, and generates a SHA‑256 checksum manifest.

Usage:
    python code/utils/download_data.py
"""
import os
import sys
import hashlib
import argparse
import logging
from pathlib import Path

import requests

# Project root (three levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def calculate_file_hash(filepath: Path) -> str:
    """Calculate SHA‑256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()


def download_file(url: str, dest: Path):
    """Download a file with streaming and write to `dest`."""
    logger.info(f"Downloading {url} → {dest}")
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    logger.info(f"Saved {dest}")


def main():
    parser = argparse.ArgumentParser(description="Download GLUE SST-2 dataset")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(PROJECT_ROOT / "data" / "raw" / "sst2"),
        help="Directory to save the downloaded dataset",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # URLs for the three splits (publicly hosted on the HuggingFace hub)
    base_url = "https://huggingface.co/datasets/glue/resolve/main/SST-2"
    files = {
        "train.tsv": f"{base_url}/train.tsv",
        "dev.tsv": f"{base_url}/dev.tsv",
        "test.tsv": f"{base_url}/test.tsv",
    }

    saved_paths = []
    for filename, url in files.items():
        dest_path = out_dir / filename
        download_file(url, dest_path)
        saved_paths.append(dest_path)

    # Generate checksum manifest
    manifest_path = out_dir / "checksums.manifest"
    logger.info(f"Generating checksum manifest at {manifest_path}")
    with open(manifest_path, "w") as mf:
        mf.write("# SHA‑256 checksums for SST-2 dataset splits\n")
        for path in saved_paths:
            file_hash = calculate_file_hash(path)
            mf.write(f"{file_hash}  {path.name}\n")
    logger.info("Checksum manifest created.")


if __name__ == "__main__":
    main()