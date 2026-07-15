from __future__ import annotations

import argparse
import hashlib
import logging
import os
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from utils.logging import get_logger
from utils.config import get_config

# Constants
GHTONENT_MANIFEST_URL = "https://storage.googleapis.com/gh-projects/manifests/java-projects.json"
DEFAULT_OUTPUT_DIR = "data/raw/gh_projects"
DEFAULT_PROJECT_COUNT = 10
CHECKSUM_ALGORITHM = "sha256"

logger = get_logger(__name__)


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA256 checksum of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify the checksum of a downloaded archive against an expected value.

    Args:
        file_path: Path to the downloaded file.
        expected_checksum: Expected SHA256 hash string.

    Returns:
        True if checksums match, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found for checksum verification: {file_path}")
        return False

    actual_checksum = compute_sha256(file_path)
    if actual_checksum.lower() == expected_checksum.lower():
        logger.info(f"Checksum verified for {file_path.name}: {actual_checksum[:16]}...")
        return True
    else:
        logger.error(
            f"Checksum mismatch for {file_path.name}!\n"
            f"Expected: {expected_checksum}\n"
            f"Actual:   {actual_checksum}"
        )
        return False


def fetch_manifest(url: str = GHTONENT_MANIFEST_URL) -> List[Dict]:
    """
    Fetch the manifest of Java projects from GHTorrent.

    Args:
        url: URL to the manifest JSON.

    Returns:
        List of project dictionaries containing name, url, checksum, etc.
    """
    logger.info(f"Fetching manifest from {url}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Manifest fetched successfully. Found {len(data)} projects.")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch manifest: {e}")
        raise


def get_java_project_files(manifest: List[Dict], count: int = DEFAULT_PROJECT_COUNT) -> List[Dict]:
    """
    Select a subset of projects from the manifest.

    Args:
        manifest: Full list of projects.
        count: Number of projects to select.

    Returns:
        List of selected project dictionaries.
    """
    if count > len(manifest):
        logger.warning(f"Requested {count} projects, but only {len(manifest)} available. Using all.")
        count = len(manifest)
    selected = manifest[:count]
    logger.info(f"Selected {count} projects for download.")
    return selected


def download_archive(url: str, dest_path: Path, checksum: str) -> Tuple[bool, Path]:
    """
    Download a single archive and verify its checksum.

    Args:
        url: Download URL.
        dest_path: Local path to save the file.
        checksum: Expected SHA256 checksum.

    Returns:
        Tuple of (success: bool, path: Path).
    """
    logger.info(f"Downloading {url} to {dest_path}...")
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()

        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Security Hardening: Verify checksum BEFORE extraction
        if verify_checksum(dest_path, checksum):
            return True, dest_path
        else:
            # Delete corrupted file
            dest_path.unlink(missing_ok=True)
            return False, dest_path

    except Exception as e:
        logger.error(f"Download failed for {url}: {e}")
        dest_path.unlink(missing_ok=True)
        return False, dest_path


def extract_archive(archive_path: Path, extract_to: Path) -> bool:
    """
    Extract a verified tar.gz archive.

    Args:
        archive_path: Path to the tar.gz file.
        extract_to: Directory to extract contents into.

    Returns:
        True if extraction successful, False otherwise.
    """
    if not archive_path.exists():
        logger.error(f"Archive not found for extraction: {archive_path}")
        return False

    logger.info(f"Extracting {archive_path.name} to {extract_to}...")
    try:
        extract_to.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive_path, "r:gz") as tar:
            # Security check: prevent path traversal (basic)
            for member in tar.getmembers():
                member_path = extract_to / member.name
                if not member_path.resolve().is_relative_to(extract_to.resolve()):
                    raise ValueError(f"Path traversal attempt detected: {member.name}")
            tar.extractall(path=extract_to)
        logger.info(f"Extraction successful: {archive_path.name}")
        return True
    except Exception as e:
        logger.error(f"Extraction failed for {archive_path}: {e}")
        return False


def run_download_pipeline(
    output_dir: Path = Path(DEFAULT_OUTPUT_DIR),
    project_count: int = DEFAULT_PROJECT_COUNT
) -> Dict[str, int]:
    """
    Run the full download and verification pipeline.

    Args:
        output_dir: Directory to store downloaded archives and extracts.
        project_count: Number of projects to process.

    Returns:
        Dictionary with counts of success/failure.
    """
    config = get_config()
    logger.info(f"Starting download pipeline for {project_count} projects...")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Fetch Manifest
    try:
        manifest = fetch_manifest()
    except Exception as e:
        logger.critical(f"Pipeline failed at manifest fetch: {e}")
        return {"success": 0, "failed": 0}

    # 2. Select Projects
    projects = get_java_project_files(manifest, project_count)

    stats = {"success": 0, "failed": 0, "checksum_failed": 0}

    for proj in projects:
        proj_name = proj.get("name", "unknown")
        url = proj.get("url")
        checksum = proj.get("checksum")

        if not url or not checksum:
            logger.warning(f"Skipping {proj_name}: missing URL or checksum in manifest.")
            stats["failed"] += 1
            continue

        archive_name = f"{proj_name}.tar.gz"
        archive_path = output_dir / archive_name
        extract_path = output_dir / proj_name

        # 3. Download
        success, path = download_archive(url, archive_path, checksum)
        if not success:
            stats["failed"] += 1
            continue

        # 4. Checksum Verified -> Extract
        # The download_archive function already verified the checksum.
        # We only proceed if it returned True.
        if extract_archive(archive_path, extract_path):
            stats["success"] += 1
            # Optional: Cleanup archive after successful extract to save space
            # archive_path.unlink(missing_ok=True)
        else:
            stats["failed"] += 1
            # Clean up failed extraction
            shutil.rmtree(extract_path, ignore_errors=True)

    logger.info(f"Pipeline completed. Success: {stats['success']}, Failed: {stats['failed']}")
    return stats


def main():
    parser = argparse.ArgumentParser(description="Download Java projects from GHTorrent with checksum verification.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to store downloads (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_PROJECT_COUNT,
        help=f"Number of projects to download (default: {DEFAULT_PROJECT_COUNT})"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )

    args = parser.parse_args()

    # Setup logging
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {args.log_level}")
    logging.basicConfig(level=numeric_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    output_path = Path(args.output_dir)
    run_download_pipeline(output_dir=output_path, project_count=args.count)


if __name__ == "__main__":
    main()