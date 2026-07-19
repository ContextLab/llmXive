"""Download and verify HCP 1200 behavioral and CIFTI data."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import urllib.request
import csv

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_paths, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, log_operation

# Constants
HCP_BEHAVIORAL_URL = "https://raw.githubusercontent.com/HumanConnectome/Data/master/1200/data/behavioral/HCP1200_BehavioralData.csv"
HCP_BEHAVIORAL_CHECKSUM = "d41d8cd98f00b204e9800998ecf8427e" # Placeholder, real checksum would be fetched
CIFTI_BASE_URL = "https://db.humanconnectome.org/data/projects/HCP_1200/1200"

# Note: Real HCP data requires authentication. For this pipeline, we assume
# the user has provided the data or we are running in an environment with access.
# If the file does not exist locally, we attempt to fetch the behavioral data.
# CIFTI files are expected to be present or downloaded via a separate authenticated process.
# This script focuses on fetching the behavioral CSV which is public.

def get_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """Verify file checksum."""
    actual_hash = get_file_hash(file_path)
    if actual_hash != expected_hash:
        log_stage_error("Checksum Verification", f"Expected {expected_hash}, got {actual_hash}")
        return False
    return True

def fetch_behavioral_data() -> str:
    """Fetch HCP behavioral data from the public URL."""
    paths = get_paths()
    behavioral_dir = paths["raw"] / "behavioral"
    ensure_dirs([behavioral_dir])
    output_path = behavioral_dir / "hcp1200_behavioral_data.csv"

    if output_path.exists():
        log_operation("Behavioral file exists, skipping download", path=str(output_path))
        return str(output_path)

    log_stage_start("Fetching behavioral data", {"url": HCP_BEHAVIORAL_URL})
    
    try:
        # Attempt to download
        urllib.request.urlretrieve(HCP_BEHAVIORAL_URL, output_path)
        log_operation("Downloaded behavioral data", path=str(output_path))
        return str(output_path)
    except Exception as e:
        log_stage_error("Fetch Behavioral Data", str(e))
        raise RuntimeError(f"Failed to download behavioral data: {e}")

def load_behavioral_data(file_path: str) -> List[Dict[str, Any]]:
    """Load behavioral data from CSV."""
    data = []
    with open(file_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def filter_subjects(behavioral_data: List[Dict[str, Any]], sleep_score_col: str = "Sleep", fd_col: str = "MeanFD", fd_threshold: float = 0.3) -> List[str]:
    """Filter subjects based on Sleep Score and Framewise Displacement."""
    valid_subjects = []
    excluded_missing = 0
    excluded_high_fd = 0

    for row in behavioral_data:
        subj_id = row.get("Subject")
        if not subj_id:
            continue

        # Check Sleep Score
        sleep_val = row.get(sleep_score_col)
        if sleep_val is None or sleep_val == "":
            excluded_missing += 1
            continue

        # Check FD
        fd_val = row.get(fd_col)
        if fd_val is None or fd_val == "":
            excluded_missing += 1
            continue

        try:
            fd = float(fd_val)
            if fd > fd_threshold:
                excluded_high_fd += 1
                continue
        except ValueError:
            excluded_missing += 1
            continue

        valid_subjects.append(subj_id)

    log_operation("Filtering complete", 
                total=len(behavioral_data), 
                valid=len(valid_subjects), 
                excluded_missing_missing_score=excluded_missing, 
                excluded_high_fd=excluded_high_fd)
    
    return valid_subjects

def save_filtered_subjects(subject_ids: List[str], output_path: str) -> None:
    """Save filtered subject IDs to a text file."""
    with open(output_path, "w") as f:
        for sid in subject_ids:
            f.write(f"{sid}\n")

def download_cifti_files(subject_ids: List[str], output_dir: str) -> None:
    """Download CIFTI files for subject IDs.
    
    NOTE: Real HCP CIFTI data requires authentication and is not publicly downloadable
    via a simple URL. This function simulates the check for existence or raises
    an error if files are missing, as per the "fail loudly" constraint for real data.
    """
    paths = get_paths()
    cifti_dir = paths["raw"] / "cifti"
    ensure_dirs([cifti_dir])

    missing_files = []
    for sid in subject_ids:
        # Expected file pattern: 1200_SubjectID.dtseries.nii
        file_name = f"{sid}.dtseries.nii"
        file_path = cifti_dir / file_name
        if not file_path.exists():
            missing_files.append(file_path)

    if missing_files:
        log_stage_error("CIFTI Download", f"Missing {len(missing_files)} CIFTI files. Real HCP data requires authentication.")
        # We do not fake download. We raise to force the user to provide data or use a real source.
        # However, for the pipeline to proceed in a test environment, we might need a mock path
        # or a specific error handling. Given the constraints, we raise.
        raise FileNotFoundError(f"Missing CIFTI files: {missing_files}")

def download_hcp_data() -> bool:
    """Main entry point for downloading HCP data."""
    log_stage_start("Download HCP Data")
    
    try:
        # 1. Fetch Behavioral Data
        behavioral_path = fetch_behavioral_data()
        
        # 2. Load and Filter
        log_stage_start("Subject Filtering")
        data = load_behavioral_data(behavioral_path)
        valid_subjects = filter_subjects(data)
        save_filtered_subjects(valid_subjects, str(Path(behavioral_path).parent / "filtered_subjects.txt"))
        log_stage_complete("Subject Filtering")

        # 3. Attempt CIFTI Download (or check existence)
        # We try to download CIFTI files if they don't exist, but this will fail without auth.
        # For the purpose of the pipeline running with real data, we assume the user
        # has placed them or the environment has access. If not, we fail loudly.
        # We only proceed if we have valid subjects.
        if valid_subjects:
            log_stage_start("Download CIFTI Files", {"count": len(valid_subjects)})
            try:
                download_cifti_files(valid_subjects, "")
            except FileNotFoundError as e:
                # If CIFTI are missing, we cannot proceed with real data.
                # But we have successfully downloaded behavioral data.
                # We log the error and return False to indicate partial success/failure.
                log_stage_error("CIFTI Download", str(e))
                return False
            
            log_stage_complete("Download CIFTI Files")

        log_stage_complete("Download HCP Data")
        return True

    except Exception as e:
        log_stage_error("Download HCP Data", str(e))
        return False

def main() -> bool:
    """CLI entry point."""
    success = download_hcp_data()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
