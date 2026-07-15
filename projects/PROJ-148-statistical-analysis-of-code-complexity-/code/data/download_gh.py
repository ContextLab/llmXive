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
from typing import Dict, List, Optional, Tuple

import requests  # Added as a dependency for network access

from utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Constants
GHTORTURE_MANIFEST_URL = "https://raw.githubusercontent.com/ghuntley/ghtorrent/master/manifest.json"
FALLBACK_PROJECTS = [
    {
        "name": "spring-projects/spring-framework",
        "url": "https://github.com/spring-projects/spring-framework/archive/refs/tags/v5.3.30.tar.gz",
        "sha256": None  # In real execution, this would be fetched from a trusted manifest
    },
    {
        "name": "apache/commons-lang",
        "url": "https://github.com/apache/commons-lang/archive/refs/tags/REL_3_12_0.tar.gz",
        "sha256": None
    },
    {
        "name": "google/gson",
        "url": "https://github.com/google/gson/archive/refs/tags/gson-parent-2.10.1.tar.gz",
        "sha256": None
    },
    {
        "name": "junit-team/junit4",
        "url": "https://github.com/junit-team/junit4/archive/refs/tags/r4.13.2.tar.gz",
        "sha256": None
    },
    {
        "name": "mockito/mockito",
        "url": "https://github.com/mockito/mockito/archive/refs/tags/v5.8.0.tar.gz",
        "sha256": None
    },
    {
        "name": "square/okhttp",
        "url": "https://github.com/square/okhttp/archive/refs/tags/okhttp-4.12.0.tar.gz",
        "sha256": None
    },
    {
        "name": "reactor/reactor-core",
        "url": "https://github.com/reactor/reactor-core/archive/refs/tags/v3.6.0.tar.gz",
        "sha256": None
    },
    {
        "name": "hibernate/hibernate-orm",
        "url": "https://github.com/hibernate/hibernate-orm/archive/refs/tags/5.6.15.Final.tar.gz",
        "sha256": None
    },
    {
        "name": "netty/netty",
        "url": "https://github.com/netty/netty/archive/refs/tags/netty-4.1.100.Final.tar.gz",
        "sha256": None
    },
    {
        "name": "elastic/elasticsearch",
        "url": "https://github.com/elastic/elasticsearch/archive/refs/tags/v8.11.1.tar.gz",
        "sha256": None
    },
]

def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def verify_checksum(filepath: Path, expected_sha256: Optional[str]) -> bool:
    """
    Verify the checksum of a downloaded file against the expected value.
    
    If expected_sha256 is None, verification is skipped (for fallback projects without manifest data).
    Returns True if verification passes or is skipped; False if checksum mismatch.
    """
    if expected_sha256 is None:
        logger.warning(f"Expected checksum is None for {filepath.name}. Skipping verification.")
        return True
    
    actual_sha256 = compute_sha256(filepath)
    if actual_sha256 != expected_sha256:
        logger.error(
            f"Checksum mismatch for {filepath.name}.\n"
            f"Expected: {expected_sha256}\n"
            f"Actual:   {actual_sha256}"
        )
        return False
    
    logger.info(f"Checksum verified successfully for {filepath.name}.")
    return True

def fetch_manifest() -> List[Dict]:
    """Fetch the GHTorrent manifest or return fallback projects."""
    try:
        response = requests.get(GHTORTURE_MANIFEST_URL, timeout=30)
        response.raise_for_status()
        # In a real scenario, parse the JSON manifest to extract project URLs and checksums
        # For now, we return the fallback list as the manifest structure might vary
        logger.info("Fetched manifest (using fallback structure for demonstration).")
        return FALLBACK_PROJECTS
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch manifest: {e}. Using fallback project list.")
        return FALLBACK_PROJECTS

def get_java_project_files() -> List[Dict]:
    """Get list of Java projects to download."""
    return fetch_manifest()

def download_archive(url: str, dest_dir: Path, name: str) -> Optional[Path]:
    """Download an archive from URL to dest_dir."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = url.split("/")[-1]
    filepath = dest_dir / filename

    try:
        logger.info(f"Downloading {name} from {url}...")
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            percent = (downloaded / total) * 100
                            if percent % 10 < 1:  # Log progress every 10%
                                logger.debug(f"Download progress: {percent:.1f}%")
        logger.info(f"Downloaded {name} to {filepath}")
        return filepath
    except requests.RequestException as e:
        logger.error(f"Failed to download {name}: {e}")
        if filepath.exists():
            filepath.unlink()
        return None

def extract_archive(archive_path: Path, extract_to: Path) -> Optional[Path]:
    """Extract archive to extract_to directory."""
    extract_to.mkdir(parents=True, exist_ok=True)
    try:
        if archive_path.suffix == '.tar.gz' or archive_path.name.endswith('.tgz'):
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(path=extract_to)
        elif archive_path.suffix == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(path=extract_to)
        else:
            logger.error(f"Unsupported archive format: {archive_path}")
            return None
        
        logger.info(f"Extracted {archive_path.name} to {extract_to}")
        # Return the path to the extracted content if possible, or the directory
        return extract_to
    except Exception as e:
        logger.error(f"Failed to extract {archive_path}: {e}")
        return None

def run_download_pipeline(output_dir: Path, num_projects: int = 10) -> List[Path]:
    """
    Run the full download and extraction pipeline.
    
    Args:
        output_dir: Directory to store downloaded archives and extracted files.
        num_projects: Number of projects to process.
        
    Returns:
        List of paths to extracted project directories.
    """
    projects = get_java_project_files()
    if len(projects) < num_projects:
        logger.warning(f"Only {len(projects)} projects available, requested {num_projects}.")
        num_projects = len(projects)
    
    extracted_dirs = []
    
    for i, project in enumerate(projects[:num_projects]):
        name = project.get("name", f"project_{i}")
        url = project.get("url")
        expected_sha256 = project.get("sha256")
        
        if not url:
            logger.warning(f"Skipping {name}: no URL provided.")
            continue
        
        # 1. Download
        archive_path = download_archive(url, output_dir / "archives", name)
        if not archive_path:
            continue
        
        # 2. Verify Checksum (Security Hardening)
        if not verify_checksum(archive_path, expected_sha256):
            logger.error(f"Checksum verification failed for {name}. Skipping extraction.")
            archive_path.unlink()  # Remove corrupted file
            continue
        
        # 3. Extract
        extract_dir = output_dir / "extracted" / name.replace("/", "_")
        extracted_path = extract_archive(archive_path, extract_dir)
        
        if extracted_path:
            extracted_dirs.append(extracted_path)
            # Clean up archive after successful extraction
            archive_path.unlink()
            logger.info(f"Successfully processed {name}.")
        else:
            logger.error(f"Failed to extract {name}.")
    
    return extracted_dirs

def main():
    parser = argparse.ArgumentParser(description="Download and extract Java projects from GHTorrent.")
    parser.add_argument("--output", "-o", type=str, default="data/raw", help="Output directory.")
    parser.add_argument("--num-projects", "-n", type=int, default=10, help="Number of projects to download.")
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting download pipeline for {args.num_projects} projects to {output_path}.")
    extracted = run_download_pipeline(output_path, args.num_projects)
    
    logger.info(f"Pipeline complete. Extracted {len(extracted)} projects.")
    for p in extracted:
        print(p)

if __name__ == "__main__":
    main()