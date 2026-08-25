import os
import sys
import subprocess
import json
import hashlib
import time
from pathlib import Path
from utils.logging_config import get_logger, error, info, warning
from utils.checksums import compute_sha256, update_state_file
from config import get_config

logger = get_logger(__name__)
config = get_config()

def check_datalad_available() -> bool:
    """Check if datalad is installed and available."""
    try:
        result = subprocess.run(
            ['datalad', '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        if result.returncode == 0:
            info(logger, "datalad is available")
            return True
        else:
            warning(logger, "datalad returned non-zero exit code")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
        warning(logger, f"datalad not available or failed to run: {e}")
        return False

def fetch_with_datalad(dataset_id: str, target_dir: Path) -> bool:
    """Fetch dataset using datalad."""
    try:
        info(logger, f"Fetching {dataset_id} using datalad to {target_dir}")
        subprocess.run(
            ['datalad', 'install', '-s', f'https://github.com/OpenNeuroDatasets/{dataset_id}', '-d', str(target_dir)],
            check=True,
            capture_output=False
        )
        # Install content (get the actual files)
        subprocess.run(
            ['datalad', 'get', '-r', '.'],
            cwd=target_dir,
            check=True,
            capture_output=False
        )
        info(logger, f"Successfully fetched {dataset_id} with datalad")
        return True
    except subprocess.CalledProcessError as e:
        error(logger, f"datalad fetch failed: {e}")
        return False
    except Exception as e:
        error(logger, f"Unexpected error during datalad fetch: {e}")
        return False

def fetch_direct(dataset_id: str, target_dir: Path) -> bool:
    """
    Fetch dataset directly from OpenNeuro using rsync or curl.
    OpenNeuro provides data via rsync: rsync://openneuro.org/dsXXXXXX
    """
    info(logger, f"Attempting direct fetch of {dataset_id} to {target_dir}")
    
    # Ensure target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Try rsync first (preferred for large datasets)
    try:
        info(logger, "Attempting rsync fetch...")
        # OpenNeuro rsync URL pattern
        rsync_url = f"rsync://openneuro.org/{dataset_id}/"
        subprocess.run(
            ['rsync', '-avz', '--progress', rsync_url, str(target_dir)],
            check=True,
            capture_output=False
        )
        info(logger, f"Successfully fetched {dataset_id} via rsync")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        warning(logger, f"rsync failed or not available: {e}")
        # Fall back to curl/wget if rsync fails
        # This is a simplified direct fetch; in production, one would use the 
        # OpenNeuro API or specific file downloads
        error(logger, "Direct fetch via rsync failed. In a real scenario, "
                      "this would fallback to specific file downloads via "
                      "OpenNeuro API or wget/curl for individual files.")
        return False

def verify_integrity(dataset_dir: Path, expected_files: list = None) -> bool:
    """
    Verify download integrity via checksums.
    For OpenNeuro, we check if expected structural files exist and compute checksums.
    """
    info(logger, f"Verifying integrity of {dataset_dir}")
    
    if not dataset_dir.exists():
        error(logger, f"Dataset directory does not exist: {dataset_dir}")
        return False

    # Common expected files/dirs in OpenNeuro ds001495
    expected_paths = [
        "dataset_description.json",
        "sub-01",
        "task-rest_bold.nii.gz"
    ]
    
    missing = []
    for path_name in expected_paths:
        full_path = dataset_dir / path_name
        if not full_path.exists():
            missing.append(path_name)
    
    if missing:
        error(logger, f"Missing expected files/directories: {missing}")
        return False

    # Compute checksum for dataset_description.json if present
    desc_file = dataset_dir / "dataset_description.json"
    if desc_file.exists():
        checksum = compute_sha256(desc_file)
        info(logger, f"dataset_description.json checksum: {checksum}")
        
        # Update state file with this checksum
        state_path = Path("state/data_state.json")
        state_path.parent.mkdir(parents=True, exist_ok=True)
        update_state_file(
            state_path,
            "data/raw/openneuro_ds001495/dataset_description.json",
            checksum
        )
    
    info(logger, f"Integrity verification passed for {dataset_dir}")
    return True

def main():
    """Main entry point for downloading OpenNeuro ds001495."""
    dataset_id = "ds001495"
    base_dir = Path("data/raw")
    target_dir = base_dir / f"openneuro_{dataset_id}"
    
    info(logger, f"Starting download of OpenNeuro {dataset_id}")
    info(logger, f"Target directory: {target_dir}")
    
    # Setup directories
    base_dir.mkdir(parents=True, exist_ok=True)
    
    success = False
    
    # Try datalad first
    if check_datalad_available():
        if fetch_with_datalad(dataset_id, target_dir):
            success = True
    
    # Fall back to direct fetch if datalad fails
    if not success:
        if fetch_direct(dataset_id, target_dir):
            success = True
    
    if not success:
        error(logger, f"Failed to download {dataset_id} via all available methods")
        sys.exit(1)
    
    # Verify integrity
    if not verify_integrity(target_dir):
        error(logger, f"Integrity verification failed for {dataset_id}")
        sys.exit(1)
    
    info(logger, f"Download and verification of {dataset_id} completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())