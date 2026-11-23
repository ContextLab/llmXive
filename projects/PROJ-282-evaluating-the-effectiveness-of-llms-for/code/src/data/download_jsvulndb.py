import os
import sys
import json
import hashlib
import logging
import shutil
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import shared utilities from the project
from src.utils.logger import get_logger, log_stage_complete, log_stage_failure
from src.utils.hash_artifacts import compute_sha256, load_current_state, save_state

# Constants
JSVULNDB_BASE_URL = "https://raw.githubusercontent.com/JSVulnDB/JSVulnDB/main/data"
# The JSVulnDB dataset is typically hosted as a collection of JSON/CSV files or a git repo.
# We target the specific subset for JavaScript vulnerabilities.
# Based on standard JSVulnDB structure, we fetch the main vulnerability list.
JSVULNDB_FILES = [
    "vulnerabilities.json", 
    "samples.json"
]

# If the direct raw files are not available, we attempt to clone the repo if git is present.
# However, for this implementation, we assume the primary source is the direct JSON files 
# or a specific archive URL provided in research.md. Since research.md is not fully provided here,
# we use the canonical GitHub raw content path.
# Fallback: If the repo is available as a zip, we use that.
REPO_ZIP_URL = "https://github.com/JSVulnDB/JSVulnDB/archive/refs/heads/main.zip"

logger = get_logger(__name__)

def ensure_output_dir(output_dir: Path) -> None:
    """Ensure the output directory exists."""
    output_dir.mkdir(parents=True, exist_ok=True)

def compute_sha256_file(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: Path, timeout: int = 300) -> bool:
    """Download a file from a URL to a destination path."""
    try:
        logger.info(f"Downloading {url} to {dest_path}")
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def load_checksums(checksums_path: Path) -> Dict[str, str]:
    """Load existing checksums from a JSON file."""
    if checksums_path.exists():
        with open(checksums_path, 'r') as f:
            return json.load(f)
    return {}

def save_checksums(checksums_path: Path, checksums: Dict[str, str]) -> None:
    """Save checksums to a JSON file."""
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def update_global_checksums(checksums_path: Path, filename: str, file_hash: str) -> None:
    """Update the global checksums file with a new entry."""
    current_checksums = load_checksums(checksums_path)
    current_checksums[filename] = file_hash
    save_checksums(checksums_path, current_checksums)
    logger.info(f"Updated checksums for {filename}")

def download_jsvulndb_subset(output_dir: Path, checksums_path: Path) -> List[Dict[str, Any]]:
    """
    Download the JSVulnDB JavaScript subset.
    Returns a list of downloaded file metadata.
    """
    ensure_output_dir(output_dir)
    downloaded_files = []

    # Strategy: Try to download the main JSON file containing vulnerability data.
    # JSVulnDB is often distributed as a single large JSON or a set of CSVs.
    # We attempt to fetch the main vulnerabilities JSON.
    primary_file = "vulnerabilities.json"
    url = f"{JSVULNDB_BASE_URL}/{primary_file}"
    dest_path = output_dir / primary_file

    success = download_file(url, dest_path)
    
    if success and dest_path.exists() and dest_path.stat().st_size > 0:
        file_hash = compute_sha256_file(dest_path)
        update_global_checksums(checksums_path, primary_file, file_hash)
        downloaded_files.append({
            "filename": primary_file,
            "path": str(dest_path),
            "hash": file_hash,
            "size_bytes": dest_path.stat().st_size
        })
        logger.info(f"Successfully downloaded and checksummed {primary_file}")
    else:
        # Fallback: If the specific file is missing, try to download the repo zip and extract
        logger.warning(f"Primary file {primary_file} not available. Attempting repo zip download.")
        zip_dest = output_dir / "jsvulndb_temp.zip"
        if download_file(REPO_ZIP_URL, zip_dest):
            # Extract logic would go here if needed, but for this task we focus on the raw file
            # If the zip is downloaded, we can rename it or extract the relevant part.
            # For simplicity, we treat the zip as the artifact if the JSON fails, 
            # but the spec asks for "raw files".
            # Let's try to find a specific JS subset file if it exists in the repo structure.
            # Assuming a standard structure: JSVulnDB/main/data/js_vulnerabilities.json
            alt_url = f"{JSVULNDB_BASE_URL}/js_vulnerabilities.json"
            alt_dest = output_dir / "js_vulnerabilities.json"
            if download_file(alt_url, alt_dest):
                file_hash = compute_sha256_file(alt_dest)
                update_global_checksums(checksums_path, alt_dest.name, file_hash)
                downloaded_files.append({
                    "filename": alt_dest.name,
                    "path": str(alt_dest),
                    "hash": file_hash,
                    "size_bytes": alt_dest.stat().st_size
                })
                logger.info(f"Successfully downloaded alternative subset {alt_dest.name}")
            else:
                logger.error("Failed to download alternative JS subset. Aborting.")
                return []
        else:
            logger.error("Failed to download repo zip. Aborting.")
            return []

    return downloaded_files

def run_download_jsvulndb() -> Dict[str, Any]:
    """Main entry point for downloading JSVulnDB."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    checksums_path = data_raw_dir / "checksums.json"

    ensure_output_dir(data_raw_dir)

    log_stage_start("T011_JSVDLDB_DOWNLOAD")
    
    try:
        downloaded = download_jsvulndb_subset(data_raw_dir, checksums_path)
        
        if not downloaded:
            log_stage_failure("T011_JSVDLDB_DOWNLOAD", "No files downloaded.")
            return {"status": "failed", "reason": "No files downloaded"}

        log_stage_complete("T011_JSVDLDB_DOWNLOAD", f"Downloaded {len(downloaded)} files.")
        return {
            "status": "success",
            "files": downloaded,
            "checksums_updated": True
        }
    except Exception as e:
        log_stage_failure("T011_JSVDLDB_DOWNLOAD", str(e))
        return {"status": "failed", "reason": str(e)}

def main():
    """CLI entry point."""
    result = run_download_jsvulndb()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") == "success" else 1)

if __name__ == "__main__":
    main()
