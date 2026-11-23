import os
import sys
import subprocess
import hashlib
import shutil
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import project utilities from the API surface
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure
from src.utils.hash_artifacts import compute_sha256
from src.utils.config import get_project_root

logger = get_logger(__name__)

# Constants
JULIET_REPO_URL = "https://github.com/nasa/juliet-testsuite.git"
JULIET_CLONE_DIR = "juliet-testsuite"
C_CPP_SUBDIR = "C_C++"
OUTPUT_RAW_DIR = "data/raw"

def ensure_output_dir():
    """Ensure the data/raw directory exists."""
    raw_dir = get_project_root() / OUTPUT_RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir

def compute_sha256_file(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def clone_juliet_repo(target_dir: Path) -> bool:
    """Clone the NIST Juliet repository if not already present."""
    if target_dir.exists():
        logger.info(f"Repository already exists at {target_dir}. Skipping clone.")
        return True
    
    try:
        logger.info(f"Cloning Juliet repository from {JULIET_REPO_URL}...")
        subprocess.run(
            ["git", "clone", JULIET_REPO_URL, str(target_dir)],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Repository cloned successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repository: {e.stderr}")
        return False

def extract_c_cpp_test_cases(clone_dir: Path, output_dir: Path) -> List[Path]:
    """
    Extract C/C++ test cases from the cloned repository.
    The Juliet suite contains many languages; we filter for C and C++.
    We copy the relevant test cases to data/raw.
    """
    c_cpp_path = clone_dir / C_CPP_SUBDIR
    if not c_cpp_path.exists():
        logger.error(f"C/C++ directory not found in repository: {c_cpp_path}")
        return []

    test_case_files = []
    # Walk the directory tree to find source files
    # Juliet organizes by CWE, then test case ID, then variant
    for root, dirs, files in os.walk(c_cpp_path):
        for file in files:
            if file.endswith(('.c', '.cpp', '.cc', '.cxx')):
                src_path = Path(root) / file
                # Determine relative path to preserve structure or flatten
                # For simplicity and to match T010a style, we flatten with a prefix
                rel_path = src_path.relative_to(c_cpp_path)
                # Create a unique filename: <cwe>_<id>_<variant>.<ext>
                # e.g., cwe789_001_001.c
                # Parse the directory structure: usually .../CWE789_001/001/001.c
                # We'll just copy the file with a sanitized name
                safe_name = f"{rel_path.parent.name}_{file}"
                # Replace path separators with underscores for safety
                safe_name = safe_name.replace(os.sep, "_").replace("/", "_")
                
                dest_path = output_dir / safe_name
                if not dest_path.exists():
                    shutil.copy2(src_path, dest_path)
                    test_case_files.append(dest_path)
                else:
                    logger.warning(f"File already exists: {dest_path}, skipping.")
    
    logger.info(f"Extracted {len(test_case_files)} C/C++ test cases.")
    return test_case_files

def generate_checksums(file_paths: List[Path]) -> Dict[str, str]:
    """Generate checksums for a list of files."""
    checksums = {}
    for file_path in file_paths:
        checksum = compute_sha256_file(file_path)
        checksums[file_path.name] = checksum
    return checksums

def update_global_checksums(new_checksums: Dict[str, str], global_checksums_path: Path):
    """Update the global checksums.json file with new entries."""
    if global_checksums_path.exists():
        with open(global_checksums_path, 'r') as f:
            global_data = json.load(f)
    else:
        global_data = {}

    global_data["juliet_c_cpp"] = new_checksums

    with open(global_checksums_path, 'w') as f:
        json.dump(global_data, f, indent=2)
    
    logger.info(f"Updated global checksums at {global_checksums_path}")

def run_download_juliet():
    """Main logic to download and process Juliet dataset."""
    project_root = get_project_root()
    raw_dir = ensure_output_dir()
    clone_target = project_root / JULIET_CLONE_DIR
    checksums_file = raw_dir / "checksums.json"

    log_stage_start("download_nist_juliet")

    # 1. Clone Repository
    if not clone_juliet_repo(clone_target):
        log_stage_failure("download_nist_juliet", "Failed to clone repository")
        return False

    # 2. Extract C/C++ subset
    extracted_files = extract_c_cpp_test_cases(clone_target, raw_dir)
    if not extracted_files:
        log_stage_failure("download_nist_juliet", "No C/C++ test cases found or extracted.")
        return False

    # 3. Generate Checksums
    checksums = generate_checksums(extracted_files)

    # 4. Update Global Checksums
    update_global_checksums(checksums, checksums_file)

    # 5. Verification
    # Verify that the files exist and checksums match
    for fname, expected_hash in checksums.items():
        fpath = raw_dir / fname
        if not fpath.exists():
            log_stage_failure("download_nist_juliet", f"File {fname} missing after extraction.")
            return False
        actual_hash = compute_sha256_file(fpath)
        if actual_hash != expected_hash:
            log_stage_failure("download_nist_juliet", f"Checksum mismatch for {fname}.")
            return False

    log_stage_complete("download_nist_juliet", f"Downloaded {len(extracted_files)} files to {raw_dir}")
    return True

def main():
    """Entry point for the script."""
    success = run_download_juliet()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
