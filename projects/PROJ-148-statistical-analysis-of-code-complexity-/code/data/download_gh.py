from __future__ import annotations

import argparse
import hashlib
import logging
import os
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import requests
from utils.logging import get_logger
from utils.config import get_config

# -------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------
GHTONENT_MANIFEST_URL = "https://storage.googleapis.com/gh-projects/manifests/java-projects.json"
GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
DEFAULT_OUTPUT_DIR = "data/raw"
DEFAULT_PROJECT_COUNT = 10
CHECKSUM_ALGORITHM = "sha256"

logger = get_logger(__name__)

# -------------------------------------------------------------------------
# Helper utilities
# -------------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Compute the SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: Path, expected_checksum: Optional[str]) -> bool:
    """
    Verify the checksum of a downloaded archive against an expected value.

    If ``expected_checksum`` is ``None`` the function returns ``True`` (no
    verification possible). This is used for the GitHub fallback where the
    checksum is not known ahead of time.
    """
    if expected_checksum is None:
        logger.debug(f"No expected checksum provided for {file_path.name}; skipping verification.")
        return True

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


# -------------------------------------------------------------------------
# Manifest handling (primary GHTorrent source)
# -------------------------------------------------------------------------
def fetch_manifest(url: str = GHTONENT_MANIFEST_URL) -> List[Dict]:
    """Fetch the manifest of Java projects from GHTorrent."""
    logger.info(f"Fetching manifest from {url}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Manifest fetched successfully. Found {len(data)} projects.")
        return data
    except requests.exceptions.RequestException as e:
        logger.warning(f"Unable to fetch GHTorrent manifest: {e}")
        raise


def get_java_project_files(manifest: List[Dict], count: int = DEFAULT_PROJECT_COUNT) -> List[Dict]:
    """Select a subset of projects from the manifest."""
    if count > len(manifest):
        logger.warning(f"Requested {count} projects, but only {len(manifest)} available. Using all.")
        count = len(manifest)
    selected = manifest[:count]
    logger.info(f"Selected {count} projects for download (GHTorrent).")
    return selected


# -------------------------------------------------------------------------
# GitHub fallback handling
# -------------------------------------------------------------------------
def fallback_search_java_projects(count: int = DEFAULT_PROJECT_COUNT) -> List[Dict]:
    """
    Search GitHub for popular Java repositories and return a list of dicts
    compatible with the primary pipeline (keys: ``name``, ``url``, ``checksum``).
    """
    logger.info(f"Falling back to GitHub search for {count} Java projects.")
    params = {
        "q": "language:Java",
        "sort": "stars",
        "order": "desc",
        "per_page": count,
    }
    try:
        resp = requests.get(GITHUB_SEARCH_URL, params=params, timeout=30)
        resp.raise_for_status()
        results = resp.json()
        items = results.get("items", [])
        projects = []
        for item in items:
            full_name = item["full_name"]  # e.g. "owner/repo"
            # Use the archive URL for the default branch (usually master/main)
            archive_url = f"https://api.github.com/repos/{full_name}/zipball/master"
            projects.append(
                {
                    "name": full_name.replace("/", "_"),
                    "url": archive_url,
                    "checksum": None,  # unknown until after download
                }
            )
        logger.info(f"Found {len(projects)} Java projects via GitHub.")
        return projects
    except requests.exceptions.RequestException as e:
        logger.error(f"GitHub search failed: {e}")
        raise


# -------------------------------------------------------------------------
# Download / extraction helpers
# -------------------------------------------------------------------------
def download_archive(url: str, dest_path: Path, checksum: Optional[str]) -> Tuple[bool, Path]:
    """
    Download a single archive and optionally verify its checksum.

    For the GitHub fallback ``checksum`` will be ``None``; the function will
    skip verification and return ``True``.
    """
    logger.info(f"Downloading {url} to {dest_path}...")
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()

        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Verify checksum if we have an expected value
        if verify_checksum(dest_path, checksum):
            return True, dest_path
        else:
            dest_path.unlink(missing_ok=True)
            return False, dest_path

    except Exception as e:
        logger.error(f"Download failed for {url}: {e}")
        dest_path.unlink(missing_ok=True)
        return False, dest_path


def extract_archive(archive_path: Path, extract_to: Path) -> bool:
    """
    Extract a verified archive (tar.gz or zip) into ``extract_to``.
    """
    if not archive_path.exists():
        logger.error(f"Archive not found for extraction: {archive_path}")
        return False

    logger.info(f"Extracting {archive_path.name} to {extract_to}...")
    try:
        extract_to.mkdir(parents=True, exist_ok=True)
        if archive_path.suffixes[-2:] == [".tar", ".gz"]:
            # tar.gz archive
            with tarfile.open(archive_path, "r:gz") as tar:
                for member in tar.getmembers():
                    member_path = extract_to / member.name
                    if not member_path.resolve().is_relative_to(extract_to.resolve()):
                        raise ValueError(f"Path traversal attempt detected: {member.name}")
                tar.extractall(path=extract_to)
        elif archive_path.suffix == ".zip":
            # zip archive
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                for member in zip_ref.namelist():
                    member_path = extract_to / member
                    if not member_path.resolve().is_relative_to(extract_to.resolve()):
                        raise ValueError(f"Path traversal attempt detected: {member}")
                zip_ref.extractall(path=extract_to)
        else:
            logger.error(f"Unsupported archive format: {archive_path.name}")
            return False

        logger.info(f"Extraction successful: {archive_path.name}")
        return True
    except Exception as e:
        logger.error(f"Extraction failed for {archive_path}: {e}")
        return False


def write_checksum_record(project_name: str, checksum: str, output_dir: Path) -> None:
    """
    Append a checksum record for a downloaded project to ``data/raw/ghtorrent_checksum.txt``.
    """
    record_path = output_dir / "ghtorrent_checksum.txt"
    line = f"{project_name}.tar.gz  {checksum}\n"
    with open(record_path, "a", encoding="utf-8") as f:
        f.write(line)
    logger.info(f"Wrote checksum record for {project_name} to {record_path}")


# -------------------------------------------------------------------------
# Main pipeline
# -------------------------------------------------------------------------
def run_download_pipeline(
    output_dir: Path = Path(DEFAULT_OUTPUT_DIR),
    project_count: int = DEFAULT_PROJECT_COUNT,
) -> Dict[str, int]:
    """
    Run the full download and verification pipeline.

    Attempts the GHTorrent manifest first; on failure falls back to a GitHub
    search for popular Java repositories.
    """
    config = get_config()
    logger.info(f"Starting download pipeline for {project_count} projects...")
    output_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------
    # 1. Obtain project list (primary -> fallback)
    # -----------------------------------------------------------------
    try:
        manifest = fetch_manifest()
        projects = get_java_project_files(manifest, project_count)
    except Exception:
        # Primary source failed – use GitHub fallback
        projects = fallback_search_java_projects(project_count)

    stats = {"success": 0, "failed": 0, "checksum_failed": 0}

    for proj in projects:
        proj_name = proj.get("name", "unknown")
        url = proj.get("url")
        checksum = proj.get("checksum")  # May be None for fallback

        if not url:
            logger.warning(f"Skipping {proj_name}: missing download URL.")
            stats["failed"] += 1
            continue

        archive_name = f"{proj_name}.tar.gz" if url.endswith(".tar.gz") else f"{proj_name}.zip"
        archive_path = output_dir / archive_name
        extract_path = output_dir / proj_name

        # -------------------------------------------------------------
        # 2. Download
        # -------------------------------------------------------------
        success, _ = download_archive(url, archive_path, checksum)
        if not success:
            logger.error(f"Download or checksum verification failed for {proj_name}.")
            stats["checksum_failed"] += 1
            continue

        # -------------------------------------------------------------
        # 3. Extract
        # -------------------------------------------------------------
        if not extract_archive(archive_path, extract_path):
            logger.error(f"Extraction failed for {proj_name}.")
            stats["failed"] += 1
            shutil.rmtree(extract_path, ignore_errors=True)
            continue

        # -------------------------------------------------------------
        # 4. Record checksum (compute if we didn't have one)
        # -------------------------------------------------------------
        final_checksum = checksum or compute_sha256(archive_path)
        write_checksum_record(proj_name, final_checksum, output_dir)

        stats["success"] += 1
        # Optional: keep the archive or delete to save space
        # archive_path.unlink(missing_ok=True)

    logger.info(
        f"Pipeline completed. Success: {stats['success']}, "
        f"Failed: {stats['failed']}, Checksum failures: {stats['checksum_failed']}"
    )
    return stats


# -------------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download Java projects from GHTorrent (or GitHub fallback) with checksum verification."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to store downloads (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--project-count",
        type=int,
        default=DEFAULT_PROJECT_COUNT,
        help=f"Number of projects to download (default: {DEFAULT_PROJECT_COUNT})",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )

    args = parser.parse_args()

    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {args.log_level}")
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    output_path = Path(args.output_dir)
    run_download_pipeline(output_dir=output_path, project_count=args.project_count)


if __name__ == "__main__":
    main()