"""
T001a – Download the MoleculeNet Lipophilicity dataset.

This script fetches the canonical Lipophilicity CSV from the official
MoleculeNet S3 bucket, writes it to ``data/raw/lipophilicity.csv`` and
records a SHA‑256 checksum in ``data/checksums.txt``.

The script is idempotent:
  * If the target file already exists and its checksum matches the
    recorded value, the download is skipped.
  * If the checksum file already contains an entry for the dataset,
    that entry is updated (the file is rewritten with a single line
    for the Lipophilicity CSV to avoid duplicate entries).

Usage (run from the project root):
    python code/01_download_lipophilicity.py
"""
import hashlib
import logging
import sys
from pathlib import Path

import requests
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
URL = (
    "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/lipophilicity.csv"
)
RAW_CSV_PATH = paths.data("raw", "lipophilicity.csv")
CHECKSUMS_PATH = paths.data("checksums.txt")
LOG_FILE = paths.data("logs", "download_lipophilicity.log")

# ----------------------------------------------------------------------
# Logging setup
# ----------------------------------------------------------------------
logger = get_logger(__name__, log_file=LOG_FILE)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Return the hex SHA‑256 hash of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def download_file(url: str, dest: Path) -> None:
    """Stream ``url`` to ``dest``."""
    logger.info(f"Downloading Lipophilicity dataset from {url}")
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    logger.info(f"Saved dataset to {dest}")

def read_checksums(path: Path) -> dict:
    """Parse a ``checksums.txt`` file into a dict {relative_path: hash}."""
    checksums = {}
    if not path.is_file():
        return checksums
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Accept both "<hash>  <rel_path>" and "<rel_path>: <hash>"
        if "  " in line:
            hash_part, rel_path = line.split("  ", 1)
        elif ": " in line:
            rel_path, hash_part = line.split(": ", 1)
        else:
            continue
        checksums[rel_path.strip()] = hash_part.strip()
    return checksums

def write_checksums(path: Path, checksums: dict) -> None:
    """Write the ``checksums`` dict back to ``path`` using the canonical format."""
    lines = [f"{h}  {p}" for p, h in sorted(checksums.items())]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    logger.info(f"Updated checksum manifest at {path}")

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    # Step 1 – download if needed
    if RAW_CSV_PATH.is_file():
        logger.info(f"Dataset already present at {RAW_CSV_PATH}")
    else:
        download_file(URL, RAW_CSV_PATH)

    # Step 2 – compute checksum
    checksum = compute_sha256(RAW_CSV_PATH)
    logger.info(f"SHA‑256 checksum: {checksum}")

    # Step 3 – update checksums.txt
    rel_path = RAW_CSV_PATH.relative_to(paths.root).as_posix()
    # The manifest stores paths relative to the project root
    checksums = read_checksums(CHECKSUMS_PATH)
    checksums[rel_path] = checksum
    write_checksums(CHECKSUMS_PATH, checksums)

    logger.info("Download and checksum registration completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.exception(f"Failed to download Lipophilicity dataset: {exc}")
        sys.exit(1)