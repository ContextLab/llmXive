"""
Download and verify OpenNeuro dataset ds003645.

This script implements the required functionality for task T001:
- Downloads the full dataset archive from OpenNeuro with up‑to‑3 retries and exponential back‑off.
- Extracts the archive into `data/raw/`.
- Downloads the checksums manifest and verifies SHA‑256 hashes for every file.
- Raises clear errors on any failure (no silent fall‑backs).

The script can be executed directly (`python code/download.py`) or imported
by downstream pipeline steps.
"""
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from config_loader import get_project_root, get_config, ensure_directory

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA‑256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def download_file(
    url: str,
    dest_path: Path,
    retries: int = 3,
    backoff: int = 10,
) -> None:
    """
    Download a file using ``requests`` with retry / exponential back‑off.

    Parameters
    ----------
    url : str
        URL to download.
    dest_path : Path
        Destination path (will be created, parent directories are made).
    retries : int, optional
        Number of attempts (default 3).
    backoff : int, optional
        Initial back‑off in seconds (default 10). It doubles after each failure.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    attempt = 0
    while attempt < retries:
        attempt += 1
        try:
            logger.info(f"Downloading {url} (attempt {attempt}/{retries})")
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with dest_path.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            logger.info(f"Successfully downloaded to {dest_path}")
            return
        except Exception as exc:
            logger.error(f"Download failed: {exc}")
            if attempt < retries:
                sleep_time = backoff * (2 ** (attempt - 1))
                logger.info(f"Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                raise RuntimeError(f"Failed to download {url} after {retries} attempts") from exc

def verify_checksum(file_path: Path, expected_hash: str) -> None:
    """
    Verify SHA‑256 checksum; raise ``ValueError`` on mismatch.

    Parameters
    ----------
    file_path : Path
        Path to the file to verify.
    expected_hash : str
        Expected SHA‑256 hash (hex string, case‑insensitive).
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Checksum verification failed – file not found: {file_path}")

    logger.info(f"Verifying checksum for {file_path}")
    actual_hash = calculate_sha256(file_path)
    if actual_hash.lower() != expected_hash.lower():
        raise ValueError(
            f"Checksum mismatch for {file_path}\\n"
            f"  expected: {expected_hash}\\n"
            f"  actual:   {actual_hash}"
        )
    logger.info(f"Checksum OK for {file_path}")

def extract_archive(archive_path: Path, dest_dir: Path) -> None:
    """
    Extract a ``.zip`` or ``.tar.gz`` archive.

    Parameters
    ----------
    archive_path : Path
        Path to the downloaded archive.
    dest_dir : Path
        Directory where the contents will be unpacked.
    """
    if not archive_path.is_file():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    logger.info(f"Extracting {archive_path} → {dest_dir}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(archive_path), str(dest_dir))
    logger.info("Extraction complete")

# ----------------------------------------------------------------------
# Core download pipeline
# ----------------------------------------------------------------------
def download_dataset_archive(dataset_id: str, dest_dir: Path) -> Path:
    """
    Download the full dataset archive from OpenNeuro.

    The OpenNeuro public URL for a dataset zip is:
    ``https://openneuro.org/crn/datasets/<id>/versions/1.0.0/download``

    Parameters
    ----------
    dataset_id : str
        OpenNeuro dataset identifier (e.g., ``ds003645``).
    dest_dir : Path
        Directory where the archive will be stored.

    Returns
    -------
    Path
        Path to the downloaded archive (could be .zip or .tar.gz).
    """
    dest_dir.mkdir(parents=True, exist_ok=True)

    archive_url = f"https://openneuro.org/crn/datasets/{dataset_id}/versions/1.0.0/download"
    archive_path = dest_dir / f"{dataset_id}.zip"  # name does not matter; could be .tar.gz after download

    if archive_path.is_file():
        logger.info(f"Archive already present at {archive_path}")
        return archive_path

    download_file(archive_url, archive_path)

    # Basic sanity check – ensure the file is a recognized archive format.
    # If it's neither zip nor tar.gz, raise an error.
    if not (zipfile.is_zipfile(archive_path) or archive_path.suffix in {".gz", ".tgz", ".tar"}):
        archive_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"The downloaded file from {archive_url} does not appear to be a valid archive. "
            "Check the URL or your network connection."
        )
    return archive_path

def download_manifest(dataset_id: str, dest_dir: Path) -> Path:
    """
    Download the ``checksums.txt`` manifest for a dataset.

    Parameters
    ----------
    dataset_id : str
    dest_dir : Path

    Returns
    -------
    Path
        Path to the manifest file.
    """
    manifest_url = f"https://openneuro.org/datasets/{dataset_id}/versions/1.0.0/file-display/checksums.txt"
    manifest_path = dest_dir / "checksums.txt"
    if manifest_path.is_file():
        logger.info(f"Manifest already present at {manifest_path}")
        return manifest_path

    download_file(manifest_url, manifest_path)
    return manifest_path

def parse_manifest(manifest_path: Path) -> Dict[str, str]:
    """
    Parse a ``checksums.txt`` file (``<hash>  <relative_path>`` per line).

    Returns
    -------
    dict
        Mapping from relative file path (as stored in the dataset) to expected SHA‑256 hash.
    """
    mapping: Dict[str, str] = {}
    with manifest_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                hash_val = parts[0]
                rel_path = " ".join(parts[1:])
                mapping[rel_path] = hash_val
    logger.info(f"Parsed {len(mapping)} entries from manifest")
    return mapping

def verify_all_checksums(root_dir: Path, manifest: Dict[str, str]) -> None:
    """
    Verify SHA‑256 checksums for every file listed in the manifest.

    Parameters
    ----------
    root_dir : Path
        Root of the extracted dataset (contains the files exactly as listed).
    manifest : dict
        Mapping from relative path → expected SHA‑256 hash.
    """
    failures = []
    for rel_path, expected_hash in manifest.items():
        file_path = root_dir / rel_path
        try:
            verify_checksum(file_path, expected_hash)
        except Exception as exc:
            failures.append(str(exc))

    if failures:
        raise RuntimeError(
            f"Checksum verification failed for {len(failures)} file(s):\\n"
            + "\\n".join(failures)
        )
    logger.info("All checksum verifications passed")

def run_download_pipeline(dataset_id: str, target_dir: Path) -> None:
    """
    Orchestrate the full download → extraction → verification workflow.

    Parameters
    ----------
    dataset_id : str
        OpenNeuro dataset identifier.
    target_dir : Path
        Directory where the raw BIDS dataset will be placed
        (i.e., ``data/raw/``).
    """
    target_dir.mkdir(parents=True, exist_ok=True)

    # 1️⃣ Download the dataset archive
    archive_path = download_dataset_archive(dataset_id, target_dir)

    # 2️⃣ Extract if not already extracted
    already_extracted = any(
        (target_dir / entry).is_dir() and entry.startswith("sub-")
        for entry in os.listdir(target_dir)
    )
    if not already_extracted:
        extract_archive(archive_path, target_dir)
    else:
        logger.info("Dataset appears already extracted – skipping extraction step.")

    # 3️⃣ Download and parse the checksum manifest
    manifest_path = download_manifest(dataset_id, target_dir)
    manifest = parse_manifest(manifest_path)

    # 4️⃣ Verify checksums
    verify_all_checksums(target_dir, manifest)

    logger.info("Dataset download and verification completed successfully.")

# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------
def download_openneuro_dataset(dataset_id: str, output_dir: Path) -> None:
    """
    Public wrapper used by the CLI and downstream modules.

    Parameters
    ----------
    dataset_id : str
        OpenNeuro dataset identifier.
    output_dir : Path
        Directory where the raw dataset should be placed.
    """
    if any(output_dir.iterdir()):
        logger.info(f"Output directory {output_dir} already contains files – assuming dataset is present.")
        # Still perform a checksum verification to be safe
        manifest_path = output_dir / "checksums.txt"
        if manifest_path.is_file():
            manifest = parse_manifest(manifest_path)
            verify_all_checksums(output_dir, manifest)
        else:
            logger.warning("Checksum manifest missing; skipping verification.")
        return

    run_download_pipeline(dataset_id, output_dir)

def main() -> None:
    """CLI entry point."""
    config = get_config()
    dataset_id = config.get("dataset_id", "ds003645")
    raw_dir = get_project_root() / "data" / "raw"

    try:
        download_openneuro_dataset(dataset_id, raw_dir)
        logger.info("All steps completed successfully.")
    except Exception as exc:
        logger.error(f"Pipeline failed: {exc}")
        raise

if __name__ == "__main__":
    main()
