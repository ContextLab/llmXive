from __future__ import annotations

import argparse
import hashlib
import logging
import os
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests

from utils.logging import get_logger

# Configuration constants
GHTONT_MANIFEST_URL = "https://storage.googleapis.com/gh-issues/manifests/java_projects.json"
DEFAULT_OUTPUT_DIR = "data/raw/gh_projects"
CHECKSUM_ALGORITHM = "sha256"

logger = get_logger(__name__)


def fetch_manifest(url: str = GHTONT_MANIFEST_URL) -> Dict:
    """
    Fetch the JSON manifest containing project metadata and checksums.
    
    Args:
        url: URL to the manifest file.
        
    Returns:
        Dictionary containing project metadata and checksums.
        
    Raises:
        requests.RequestException: If the manifest cannot be fetched.
    """
    logger.info(f"Fetching manifest from {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch manifest: {e}")
        raise


def get_java_project_files(manifest: Dict, min_projects: int = 10) -> List[Dict]:
    """
    Extract a list of Java projects from the manifest, ensuring a minimum count.
    
    Args:
        manifest: The loaded manifest dictionary.
        min_projects: Minimum number of projects required.
        
    Returns:
        List of project dictionaries.
        
    Raises:
        ValueError: If fewer than min_projects are available.
    """
    projects = manifest.get("projects", [])
    if len(projects) < min_projects:
        raise ValueError(
            f"Manifest contains only {len(projects)} projects, "
            f"but {min_projects} are required."
        )
    logger.info(f"Selected {len(projects)} projects from manifest")
    return projects


def download_archive(
    url: str, output_path: Path, timeout: int = 300
) -> Tuple[bool, Optional[str]]:
    """
    Download a file from a URL to the specified output path.
    
    Args:
        url: Source URL.
        output_path: Destination file path.
        timeout: Request timeout in seconds.
        
    Returns:
        Tuple of (success, error_message).
    """
    logger.info(f"Downloading {url} to {output_path}")
    try:
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True, None
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False, str(e)


def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """
    Verify the SHA-256 checksum of a file against an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_hash: Expected SHA-256 hex digest.
        
    Returns:
        True if checksum matches, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found for checksum verification: {file_path}")
        return False

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        calculated_hash = sha256_hash.hexdigest()
        
        if calculated_hash.lower() == expected_hash.lower():
            logger.info(f"Checksum verified for {file_path.name}")
            return True
        else:
            logger.error(
                f"Checksum mismatch for {file_path.name}. "
                f"Expected: {expected_hash}, Got: {calculated_hash}"
            )
            return False
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        return False


def extract_archive(archive_path: Path, dest_dir: Path) -> bool:
    """
    Extract a tar.gz archive to the destination directory.
    
    Args:
        archive_path: Path to the archive.
        dest_dir: Directory to extract contents to.
        
    Returns:
        True if extraction was successful, False otherwise.
    """
    if not archive_path.exists():
        logger.error(f"Archive not found: {archive_path}")
        return False

    logger.info(f"Extracting {archive_path} to {dest_dir}")
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive_path, "r:gz") as tar:
            # Security: prevent path traversal (zip slip)
            for member in tar.getmembers():
                member_path = dest_dir / member.name
                if not str(member_path.resolve()).startswith(str(dest_dir.resolve())):
                    logger.error(f"Path traversal attempt detected: {member.name}")
                    return False
            tar.extractall(dest_dir)
        return True
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return False


def run_download_pipeline(
    output_dir: Optional[str] = None,
    min_projects: int = 10,
    manifest_url: Optional[str] = None,
) -> List[Path]:
    """
    Execute the full download and verification pipeline.
    
    1. Fetch manifest
    2. Select projects
    3. Download archives
    4. Verify checksums BEFORE extraction
    5. Extract only valid archives
    
    Args:
        output_dir: Base directory for downloaded files.
        min_projects: Minimum number of projects to download.
        manifest_url: Optional override for manifest URL.
        
    Returns:
        List of paths to successfully extracted directories.
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    if manifest_url is None:
        manifest_url = GHTONT_MANIFEST_URL

    output_path = Path(output_dir)
    extracted_dirs = []

    # Step 1: Fetch Manifest
    try:
        manifest = fetch_manifest(manifest_url)
    except Exception as e:
        logger.error(f"Pipeline failed at manifest fetch: {e}")
        return extracted_dirs

    # Step 2: Get Project List
    try:
        projects = get_java_project_files(manifest, min_projects)
    except ValueError as e:
        logger.error(f"Pipeline failed at project selection: {e}")
        return extracted_dirs

    # Step 3 & 4: Download and Verify
    for project in projects:
        project_name = project.get("name", "unknown")
        archive_url = project.get("archive_url")
        expected_checksum = project.get("sha256")

        if not archive_url or not expected_checksum:
            logger.warning(f"Skipping {project_name}: Missing URL or checksum")
            continue

        archive_filename = f"{project_name}.tar.gz"
        archive_path = output_path / "archives" / archive_filename
        
        # Download
        success, error = download_archive(archive_url, archive_path)
        if not success:
            logger.warning(f"Skipping {project_name}: Download failed - {error}")
            continue

        # Verify Checksum BEFORE Extraction (Security Hardening)
        if not verify_checksum(archive_path, expected_checksum):
            logger.error(
                f"Skipping {project_name}: Checksum verification failed. "
                f"Archive removed for safety."
            )
            archive_path.unlink(missing_ok=True)
            continue

        # Step 5: Extract
        extract_dest = output_path / project_name
        if extract_archive(archive_path, extract_dest):
            logger.info(f"Successfully processed {project_name}")
            extracted_dirs.append(extract_dest)
        else:
            logger.error(f"Failed to extract {project_name}")
            archive_path.unlink(missing_ok=True)

    logger.info(f"Pipeline complete. Extracted {len(extracted_dirs)} projects.")
    return extracted_dirs


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Download and verify GHTorrent Java project archives."
    )
    parser.add_argument(
        "--output", "-o", type=str, default=DEFAULT_OUTPUT_DIR,
        help="Output directory for archives and extracted files."
    )
    parser.add_argument(
        "--min-projects", type=int, default=10,
        help="Minimum number of projects to process."
    )
    parser.add_argument(
        "--manifest-url", type=str, default=GHTONT_MANIFEST_URL,
        help="URL to the manifest JSON."
    )

    args = parser.parse_args()

    run_download_pipeline(
        output_dir=args.output,
        min_projects=args.min_projects,
        manifest_url=args.manifest_url,
    )


if __name__ == "__main__":
    main()