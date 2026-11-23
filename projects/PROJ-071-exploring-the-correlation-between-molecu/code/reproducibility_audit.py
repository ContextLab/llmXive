"""
Automated Reproducibility Audit Script (Task T056/T056a).

This script programmatically compares the SHA256 hashes stored in
`reproducibility_log.json` against the actual files in the `data/` directory.

If a mismatch is found, or if the log is missing, this script exits with
a non-zero status code to fail the build and block `research_accepted`.
"""
import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Add project root to path to ensure imports work if run from root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPRODUCIBILITY_LOG_PATH = PROJECT_ROOT / "reproducibility_log.json"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "data" / "audit.log")
    ]
)
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Returns the project root directory."""
    return PROJECT_ROOT


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculates the SHA256 hash of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"IO Error reading {file_path}: {e}")
        raise


def load_reproducibility_log() -> Dict[str, Any]:
    """
    Loads the reproducibility log from disk.
    
    Returns:
        Dictionary containing the log data.
        
    Raises:
        FileNotFoundError: If the log file is missing.
        json.JSONDecodeError: If the log file is malformed.
    """
    if not REPRODUCIBILITY_LOG_PATH.exists():
        raise FileNotFoundError(
            f"Reproducibility log not found at {REPRODUCIBILITY_LOG_PATH}. "
            "The pipeline must run successfully to generate this file before auditing."
        )
    
    try:
        with open(REPRODUCIBILITY_LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in reproducibility log: {e}")
        raise


def audit_hashes() -> Tuple[bool, str]:
    """
    Compares logged hashes against actual file hashes.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    logger.info("Starting automated reproducibility audit...")
    
    try:
        log_data = load_reproducibility_log()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return False, f"Failed to load reproducibility log: {e}"
    
    if "file_hashes" not in log_data:
        return False, "Reproducibility log missing 'file_hashes' key."
    
    logged_hashes = log_data["file_hashes"]
    all_passed = True
    failure_details = []
    
    for relative_path, expected_hash in logged_hashes.items():
        # Construct absolute path relative to project root
        # Ensure the path is relative to DATA_DIR or root as appropriate
        # The log usually stores paths relative to project root or data dir
        # We assume the paths in the log are relative to PROJECT_ROOT for safety
        file_path = PROJECT_ROOT / relative_path
        
        if not file_path.exists():
            msg = f"File missing: {relative_path}"
            logger.error(msg)
            all_passed = False
            failure_details.append(msg)
            continue
        
        try:
            actual_hash = calculate_file_hash(file_path)
        except Exception as e:
            msg = f"Failed to hash {relative_path}: {e}"
            logger.error(msg)
            all_passed = False
            failure_details.append(msg)
            continue
        
        if actual_hash != expected_hash:
            msg = (
                f"Hash Mismatch for {relative_path}:\n"
                f"  Expected: {expected_hash}\n"
                f"  Actual:   {actual_hash}"
            )
            logger.error(msg)
            all_passed = False
            failure_details.append(msg)
        else:
            logger.info(f"Verified: {relative_path} (OK)")
    
    if all_passed:
        return True, "All file hashes verified successfully."
    else:
        return False, f"Audit failed. Details:\n" + "\n".join(failure_details)


def main():
    """Main entry point for the audit script."""
    success, message = audit_hashes()
    
    if success:
        logger.info("AUDIT PASSED: " + message)
        sys.exit(0)
    else:
        logger.error("AUDIT FAILED: " + message)
        # Explicitly fail the build as per T035c and T056a requirements
        sys.exit(1)


if __name__ == "__main__":
    main()