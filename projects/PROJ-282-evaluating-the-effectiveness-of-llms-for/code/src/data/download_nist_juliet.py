"""
Download the NIST Juliet dataset (C/C++ subset) for vulnerability analysis.

This module fetches the official NIST Juliet repository, extracts the C/C++
test cases, and saves them to the data/raw directory. It also computes and
saves checksums for verification.

Constraints:
- Must fail loudly if the real source is unreachable (no synthetic fallback).
- Output files must be saved to data/raw/ with naming convention juliet_c_*.
"""
import os
import sys
import subprocess
import hashlib
import shutil
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure
from src.utils.hash_artifacts import compute_sha256, load_current_state, save_state

logger = get_logger(__name__)

# Configuration
JULIET_REPO_URL = "https://gitlab.com/nist-juliet/juliet-c-cpp-test-cases"
# Using a specific commit or tag for reproducibility if available, otherwise default
JULIET_REF = "main" 
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"
CHECKSUM_FILE = OUTPUT_DIR / "checksums.json"

def ensure_output_dir():
    """Ensure the output directory exists."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def compute_sha256_file(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        raise

def clone_juliet_repo(target_dir: Path):
    """Clone the NIST Juliet repository."""
    logger.info(f"Cloning Juliet repository to {target_dir}")
    if target_dir.exists():
        logger.warning(f"Target directory {target_dir} already exists. Removing it.")
        shutil.rmtree(target_dir)
    
    try:
        # Use git clone
        cmd = ["git", "clone", "--depth", "1", "--branch", JULIET_REF, JULIET_REPO_URL, str(target_dir)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Repository cloned successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repository: {e.stderr}")
        raise RuntimeError(f"Failed to clone Juliet repository: {e.stderr}")
    except FileNotFoundError:
        logger.error("Git is not installed or not in PATH. Cannot proceed.")
        raise RuntimeError("Git is required to download the Juliet dataset.")

def extract_c_cpp_test_cases(source_dir: Path, output_dir: Path):
    """
    Extract C and C++ test cases from the cloned repository.
    The Juliet repository structure typically has directories like 'c', 'c++', etc.
    We are interested in the 'c' and 'c++' folders for C/C++ code.
    """
    logger.info(f"Extracting C/C++ test cases from {source_dir}")
    
    # Common directories in Juliet for C and C++
    # Note: The exact structure might vary, but usually 'c' and 'c++' exist.
    # We will look for directories named 'c' or 'c++' inside the source_dir
    # or directly in the root if the repo is shallow.
    
    # Let's assume the structure is: <repo_root>/c/<cwe_id>/...
    # and <repo_root>/c++/<cwe_id>/...
    
    c_sources = []
    c_files = []
    
    # Walk the source directory to find .c and .cpp files
    for root, dirs, files in os.walk(source_dir):
        # Filter out hidden directories or non-code directories if necessary
        for file in files:
            if file.endswith('.c') or file.endswith('.cpp') or file.endswith('.cc'):
                full_path = Path(root) / file
                c_files.append(full_path)
    
    if not c_files:
        logger.error("No C/C++ files found in the repository. The repository structure might be different.")
        raise RuntimeError("No C/C++ test cases found in the Juliet repository.")

    logger.info(f"Found {len(c_files)} C/C++ files.")

    # Organize files into output directory
    # We will create a structure like: data/raw/juliet_c/<cwe_id>/<filename>
    # or simply flatten if structure is not critical, but preserving some structure is better.
    # Let's try to preserve the CWE directory structure if possible.
    
    juliet_c_base = output_dir / "juliet_c"
    juliet_c_base.mkdir(parents=True, exist_ok=True)
    
    extracted_count = 0
    for file_path in c_files:
        # Determine the CWE directory if possible
        # Juliet files often have 'cwe_<id>' in the path
        parts = file_path.parts
        cwe_dir = None
        for part in parts:
            if part.startswith('cwe_'):
                cwe_dir = part
                break
        
        if cwe_dir:
            dest_dir = juliet_c_base / cwe_dir
        else:
            dest_dir = juliet_c_base / "unknown_cwe"
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / file_path.name
        
        # Copy file
        shutil.copy2(file_path, dest_file)
        extracted_count += 1
        
        # Log progress every 1000 files
        if extracted_count % 1000 == 0:
            logger.info(f"Extracted {extracted_count} files...")

    logger.info(f"Successfully extracted {extracted_count} C/C++ test cases to {juliet_c_base}")
    return juliet_c_base

def generate_checksums(target_dir: Path, checksum_file: Path):
    """Generate checksums for all files in the target directory and save to JSON."""
    logger.info(f"Generating checksums for {target_dir}")
    checksums = {}
    
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(target_dir)
            file_hash = compute_sha256_file(file_path)
            checksums[str(rel_path)] = file_hash
    
    with open(checksum_file, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)
    
    logger.info(f"Checksums saved to {checksum_file}")
    return checksums

def update_global_checksums(new_checksums: Dict[str, str], global_file: Path):
    """Update the global checksums.json file with new entries."""
    global_checksums = {}
    if global_file.exists():
        with open(global_file, 'r', encoding='utf-8') as f:
            global_checksums = json.load(f)
    
    # Merge new checksums
    # We prefix the path to avoid collisions if other datasets use similar names
    for rel_path, hash_val in new_checksums.items():
        global_checksums[f"juliet_c/{rel_path}"] = hash_val
    
    with open(global_file, 'w', encoding='utf-8') as f:
        json.dump(global_checksums, f, indent=2)
    
    logger.info(f"Updated global checksums in {global_file}")

def run_download_juliet():
    """Main execution function to download and process Juliet dataset."""
    log_stage_start("download_nist_juliet")
    
    try:
        ensure_output_dir()
        
        # Temporary directory for cloning
        temp_clone_dir = PROJECT_ROOT / "data" / "raw" / "juliet_temp_clone"
        if temp_clone_dir.exists():
            shutil.rmtree(temp_clone_dir)
        
        # Clone repository
        clone_juliet_repo(temp_clone_dir)
        
        # Extract C/C++ test cases
        extracted_dir = extract_c_cpp_test_cases(temp_clone_dir, OUTPUT_DIR)
        
        # Generate checksums for the extracted dataset
        dataset_checksums = generate_checksums(extracted_dir, OUTPUT_DIR / "checksums_juliet_c.json")
        
        # Update global checksums file
        update_global_checksums(dataset_checksums, CHECKSUM_FILE)
        
        # Clean up temporary clone directory
        if temp_clone_dir.exists():
            shutil.rmtree(temp_clone_dir)
            logger.info("Cleaned up temporary clone directory.")
        
        log_stage_complete("download_nist_juliet", {
            "output_dir": str(extracted_dir),
            "checksum_file": str(OUTPUT_DIR / "checksums_juliet_c.json"),
            "global_checksum_file": str(CHECKSUM_FILE),
            "file_count": len(dataset_checksums)
        })
        
        return True
        
    except Exception as e:
        log_stage_failure("download_nist_juliet", str(e))
        raise

def main():
    """Entry point for the script."""
    run_download_juliet()

if __name__ == "__main__":
    main()
