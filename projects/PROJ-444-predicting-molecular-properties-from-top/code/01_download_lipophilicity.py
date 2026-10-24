"""
Download the MoleculeNet Lipophilicity dataset (raw SMILES + logP) and
register its SHA‑256 checksum.

This script implements task **T001a**. It fetches the dataset from the
official MoleculeNet S3 URL to ensure the canonical version is obtained,
saves it to ``data/raw/lipophilicity.csv``, and updates the checksum
manifest ``data/checksums.txt``.
"""

import argparse
import hashlib
import logging
import os
import sys
from pathlib import Path

import requests
import pandas as pd

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Return the hex SHA‑256 hash of *file_path*."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def read_checksums(path: Path) -> dict:
    """
    Parse a ``checksums.txt`` file into a ``{relative_path: hash}`` dict.
    Supports the two canonical line formats:

        <hash>  <relative_path>
        <relative_path>: <hash>
    """
    checksums = {}
    if not path.is_file():
        return checksums
    with path.open("r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "  " in line:
                h, p = line.split("  ", 1)
                checksums[p.strip()] = h.strip()
            elif ":" in line:
                p, h = line.split(":", 1)
                checksums[p.strip()] = h.strip()
    return checksums


def write_checksums(path: Path, checksums: dict) -> None:
    """Write *checksums* to *path* using the canonical two‑space format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for rel_path, h in sorted(checksums.items()):
            f.write(f"{h}  {rel_path}\n")


def setup_logger(log_file: str | None = None) -> logging.Logger:
    logger = logging.getLogger("download_lipophilicity")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        stream = logging.StreamHandler(sys.stdout)
        stream.setFormatter(formatter)
        logger.addHandler(stream)
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger


# ----------------------------------------------------------------------
# Main download routine
# ----------------------------------------------------------------------
def download_lipophilicity(csv_path: Path, logger: logging.Logger) -> None:
    """
    Download the Lipophilicity dataset from the official S3 URL,
    ensure it contains the required columns, and write it to *csv_path*.
    """
    url = "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/lipophilicity.csv"
    logger.info(f"Downloading Lipophilicity dataset from {url}...")
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

    # Load into pandas to ensure we have the correct canonical columns (smiles, logP)
    # The S3 file typically has 'smiles' and 'logP'
    from io import StringIO
    df = pd.read_csv(StringIO(response.text))
    
    if "smiles" not in df.columns:
        logger.error("Downloaded CSV missing 'smiles' column.")
        raise ValueError("Dataset missing required columns")
    
    # The S3 file may use 'logP' or 'label'. Ensure it is 'logP' for the schema.
    if "logP" not in df.columns and "label" in df.columns:
        df = df.rename(columns={"label": "logP"})
    elif "logP" not in df.columns:
        logger.error("Downloaded CSV missing 'logP' or 'label' column.")
        raise ValueError("Dataset missing target column")

    logger.info(f"Total records downloaded: {len(df)}")

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    logger.info(f"Wrote raw Lipophilicity CSV to {csv_path}")


def update_checksum(csv_path: Path, checksum_path: Path, logger: logging.Logger) -> None:
    """
    Compute the SHA‑256 checksum of *csv_path* and (idempotently) add or
    update the entry for that file in *checksum_path*.
    """
    checksum = compute_sha256(csv_path)
    # Store path relative to the project root (POSIX style)
    rel_path = csv_path.as_posix()
    logger.info(f"Computed SHA‑256 checksum: {checksum}")

    checksums = read_checksums(checksum_path)
    checksums[rel_path] = checksum
    write_checksums(checksum_path, checksums)
    logger.info(f"Updated checksum manifest at {checksum_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download the MoleculeNet Lipophilicity dataset (raw SMILES + logP)."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Directory where ``lipophilicity.csv`` will be written.",
    )
    parser.add_argument(
        "--checksum-file",
        type=str,
        default="data/checksums.txt",
        help="Path to the checksum manifest to update.",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Optional log file path.",
    )
    args = parser.parse_args()

    logger = setup_logger(args.log_file)

    csv_path = Path(args.output_dir) / "lipophilicity.csv"
    checksum_path = Path(args.checksum_file)

    # 1. Download the dataset
    download_lipophilicity(csv_path, logger)

    # 2. Compute and record checksum
    update_checksum(csv_path, checksum_path, logger)

    logger.info("Task T001a completed successfully.")


if __name__ == "__main__":
    main()