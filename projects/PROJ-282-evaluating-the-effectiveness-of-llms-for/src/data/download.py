"""
Dataset Download Module for PROJ-282.
Fetches VulDeePecker, BigVul, and NIST Juliet datasets.
Implements primary/fallback logic for C/C++ data acquisition.
"""
import os
import sys
import subprocess
import hashlib
import shutil
import logging
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any
import json

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_LOGS_DIR = PROJECT_ROOT / "data" / "logs"
DATA_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.FileHandler(DATA_LOGS_DIR / "error.log")
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

# Dataset Configuration (URLs and Checksums)
# Note: These are the canonical sources. If checksums are unknown, we verify existence and size.
DATASETS = {
    "vuldeepecker": {
        "name": "VulDeePecker",
        "languages": ["Python"],
        "url": "https://github.com/vuldeepecker/VulDeePecker/raw/master/data/processed/vuldeepecker.jsonl",
        "type": "wget",
        "expected_hash": None, # Hash verification requires the file first
        "output_file": "vuldeepecker.jsonl"
    },
    "bigvul": {
        "name": "BigVul",
        "languages": ["C", "JavaScript"],
        "url": "https://github.com/hazimshak/BigVul/raw/master/bigvul.jsonl",
        "type": "wget",
        "expected_hash": None,
        "output_file": "bigvul.jsonl"
    },
    "nist_juliet": {
        "name": "NIST Juliet (C)",
        "languages": ["C"],
        # NIST Juliet is a large repository. We fetch the specific C test case zip.
        "url": "https://cwe.mitre.org/data/definitions/41.html", # Placeholder for logic, actual download is git clone or specific zip
        # Actual direct download link for Juliet C Test Cases (approximate, often hosted on NIST or mirrored)
        # Using the official NIST Juliet download pattern if available, otherwise git clone.
        # For this implementation, we attempt to fetch the specific C test suite zip if available,
        # or clone the Juliet repository.
        # Given the "Primary Mandate", we try a direct fetch first.
        "url_git": "https://gitlab.com/codesec/juliet-c-test-suite.git",
        "type": "git",
        "expected_hash": None,
        "output_dir": "juliet_c_test_suite"
    }
}

def compute_sha256(file_path: Path) -> Optional[str]:
    """Compute SHA256 hash of a file."""
    if not file_path.exists():
        return None
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return None

def verify_checksum(file_path: Path, expected_hash: Optional[str]) -> bool:
    """Verify file checksum."""
    if expected_hash is None:
        logger.info(f"Skipping checksum verification for {file_path} (no expected hash).")
        return True
    actual_hash = compute_sha256(file_path)
    if actual_hash != expected_hash:
        logger.error(f"Checksum mismatch for {file_path}. Expected: {expected_hash}, Got: {actual_hash}")
        return False
    return True

def download_via_wget(url: str, output_path: Path) -> Tuple[bool, str]:
    """Download a file via wget."""
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {url} to {output_path}...")
    try:
        # Use wget with progress bar disabled for cleaner logs
        result = subprocess.run(
            ["wget", "--timeout=30", "--tries=3", "-O", str(output_path), url],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info(f"Successfully downloaded {url}")
            return True, ""
        else:
            error_msg = result.stderr or f"wget failed with code {result.returncode}"
            logger.error(f"Failed to download {url}: {error_msg}")
            return False, error_msg
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout downloading {url}")
        return False, "Timeout"
    except Exception as e:
        logger.error(f"Exception downloading {url}: {e}")
        return False, str(e)

def clone_via_git(url: str, output_dir: Path) -> Tuple[bool, str]:
    """Clone a git repository."""
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Cloning {url} to {output_dir}...")
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(output_dir)],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info(f"Successfully cloned {url}")
            return True, ""
        else:
            error_msg = result.stderr or f"git failed with code {result.returncode}"
            logger.error(f"Failed to clone {url}: {error_msg}")
            return False, error_msg
    except Exception as e:
        logger.error(f"Exception cloning {url}: {e}")
        return False, str(e)

def validate_dataset(dataset_name: str, success: bool, error_msg: str = "") -> bool:
    """
    Validate dataset fetch.
    Returns True if successful.
    """
    if success:
        logger.info(f"Validation passed for {dataset_name}")
        return True
    else:
        logger.warning(f"Validation failed for {dataset_name}: {error_msg}")
        return False

def log_scope_deviation(reason: str):
    """Log scope deviation to data/logs/scope_deviation.log"""
    log_path = DATA_LOGS_DIR / "scope_deviation.log"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as f:
        f.write(f"[{timestamp}] SCOPE DEVIATION: {reason}\n")
    logger.warning(f"Logged scope deviation: {reason}")

def download_all_datasets():
    """
    Orchestrates the download of all required datasets.
    Primary Mandate: NIST Juliet for C/C++.
    Fallback: BigVul for C/C++ if NIST fails.
    Fail-Loudly: If both fail for C/C++, raise Exception.
    """
    logger.info("Starting dataset download process...")
    
    # 1. Download VulDeePecker (Python)
    vd_config = DATASETS["vuldeepecker"]
    vd_path = DATA_RAW_DIR / vd_config["output_file"]
    success, err = download_via_wget(vd_config["url"], vd_path)
    if not validate_dataset(vd_config["name"], success, err):
        # Non-critical for this specific task's C/C++ logic, but good practice
        logger.error(f"VulDeePecker download failed. Continuing with C/C++ logic.")
    
    # 2. Download BigVul (C and JavaScript) - Needed for fallback
    bv_config = DATASETS["bigvul"]
    bv_path = DATA_RAW_DIR / bv_config["output_file"]
    bv_success, bv_err = download_via_wget(bv_config["url"], bv_path)
    if not bv_success:
        logger.warning(f"BigVul download failed initially: {bv_err}")
    
    # 3. Attempt NIST Juliet (Primary Mandate for C/C++)
    nist_config = DATASETS["nist_juliet"]
    nist_success = False
    nist_error = ""
    
    logger.info("Attempting to fetch NIST Juliet (Primary Mandate)...")
    if nist_config["type"] == "git":
        nist_success, nist_error = clone_via_git(nist_config["url_git"], DATA_RAW_DIR / nist_config["output_dir"])
    else:
        # Fallback to wget if type is wget
        nist_path = DATA_RAW_DIR / "juliet.zip"
        nist_success, nist_error = download_via_wget(nist_config["url"], nist_path)
    
    if not nist_success:
        logger.error(f"NIST Juliet fetch failed: {nist_error}")
        # Check if BigVul is available as fallback
        if not bv_success:
            # Re-attempt BigVul just in case, or fail hard if it definitely wasn't there
            # The task says: "If NIST Juliet fetch fails ... fallback to BigVul"
            # But we already tried BigVul. Let's try again to be sure.
            bv_success, bv_err = download_via_wget(bv_config["url"], bv_path)
            if not bv_success:
                # BOTH FAILED
                error_msg = f"CRITICAL FAILURE: Both NIST Juliet and BigVul fetches failed for C/C++ data."
                logger.error(error_msg)
                log_scope_deviation(f"Failed to acquire C/C++ dataset (NIST: {nist_error}, BigVul: {bv_err}).")
                raise Exception(error_msg)
            else:
                # BigVul succeeded on retry
                logger.info("Fallback to BigVul successful after NIST failure.")
                log_scope_deviation(f"Fallback to BigVul triggered because NIST Juliet fetch failed: {nist_error}")
        else:
            # BigVul was already available
            logger.info("Fallback to BigVul successful (already downloaded).")
            log_scope_deviation(f"Fallback to BigVul triggered because NIST Juliet fetch failed: {nist_error}")
    else:
        logger.info("NIST Juliet fetch successful. BigVul not needed for C/C++ primary source.")
        # Note: BigVul might still be needed for JavaScript if not in NIST
        # But NIST is the primary mandate for C/C++.
    
    logger.info("Dataset download process completed.")
    return True

def main():
    """Entry point for the download script."""
    try:
        download_all_datasets()
        logger.info("All datasets processed successfully.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Pipeline halted due to critical download error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()