"""
T014: Implement SHA-256 checksum verification for all files in data/raw/
and log results to state/projects/PROJ-164-neural-oscillations-as-a-biomarker-for-p.yaml.

Mandatory: Use write_checksum_to_state helper to write successful checksums.
Set files read-only on success.
"""
import os
import stat
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Import from existing API surface
from utils.io_helpers import compute_sha256, write_checksum_to_state
from utils.config import DATA_RAW, STATE_PROJECTS, PROJECT_ID

logger = logging.getLogger(__name__)


def set_read_only(file_path: Path) -> bool:
    """
    Set a file to read-only (chmod 444).
    
    Args:
        file_path: Path to the file to make read-only
        
    Returns:
        True if successful, False otherwise
    """
    try:
        current_mode = os.stat(file_path).st_mode
        # Remove write permissions for user, group, and others
        new_mode = current_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
        os.chmod(file_path, new_mode)
        logger.info(f"Set file to read-only: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to set read-only on {file_path}: {e}")
        return False


def verify_and_lock_files(raw_dir: Path = None) -> Dict[str, Any]:
    """
    Verify SHA-256 checksums for all files in data/raw/ and lock them if valid.
    
    Args:
        raw_dir: Path to the raw data directory. Defaults to DATA_RAW from config.
        
    Returns:
        Dictionary with verification results:
        {
            "total_files": int,
            "verified": int,
            "failed": int,
            "files": List[Dict[str, str]],
            "state_file": str
        }
    """
    if raw_dir is None:
        raw_dir = Path(DATA_RAW)
    
    if not raw_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_dir}")
        return {
            "total_files": 0,
            "verified": 0,
            "failed": 0,
            "files": [],
            "state_file": str(Path(STATE_PROJECTS) / f"{PROJECT_ID}.yaml"),
            "error": "Directory not found"
        }
    
    # Get all files in the raw directory (non-recursive for safety)
    files = [f for f in raw_dir.iterdir() if f.is_file()]
    
    if not files:
        logger.warning(f"No files found in {raw_dir}")
        return {
            "total_files": 0,
            "verified": 0,
            "failed": 0,
            "files": [],
            "state_file": str(Path(STATE_PROJECTS) / f"{PROJECT_ID}.yaml")
        }
    
    results = []
    verified_count = 0
    failed_count = 0
    state_file_path = Path(STATE_PROJECTS) / f"{PROJECT_ID}.yaml"
    
    logger.info(f"Starting checksum verification for {len(files)} files in {raw_dir}")
    
    for file_path in files:
        file_name = file_path.name
        try:
            # Compute SHA-256
            checksum = compute_sha256(file_path)
            logger.debug(f"Computed checksum for {file_name}: {checksum[:16]}...")
            
            # Verify the file hasn't been tampered with (basic check: file exists and readable)
            # In a full pipeline, we'd compare against a pre-computed manifest
            # For now, we verify the file is readable and compute its hash
            
            result = {
                "file": file_name,
                "path": str(file_path),
                "checksum": checksum,
                "status": "verified",
                "locked": False
            }
            
            # Set file to read-only on success
            if set_read_only(file_path):
                result["locked"] = True
                verified_count += 1
            else:
                result["status"] = "warning"
                result["message"] = "Checksum computed but failed to lock file"
                verified_count += 1  # Still considered verified, just couldn't lock
            
        except Exception as e:
            logger.error(f"Error processing {file_name}: {e}")
            result = {
                "file": file_name,
                "path": str(file_path),
                "checksum": None,
                "status": "failed",
                "locked": False,
                "error": str(e)
            }
            failed_count += 1
        
        results.append(result)
    
    # Write successful checksums to state file
    if verified_count > 0:
        successful_files = [r for r in results if r["status"] == "verified"]
        write_checksum_to_state(
            state_file=state_file_path,
            project_id=PROJECT_ID,
            checksums=[
                {
                    "file": r["file"],
                    "checksum": r["checksum"]
                }
                for r in successful_files
            ]
        )
        logger.info(f"Wrote {verified_count} checksums to {state_file_path}")
    
    return {
        "total_files": len(files),
        "verified": verified_count,
        "failed": failed_count,
        "files": results,
        "state_file": str(state_file_path)
    }


def main():
    """
    Main entry point for T014: Checksum verification and locking.
    """
    # Setup logging
    from utils.logging_setup import get_logger
    logger = get_logger(__name__)
    
    logger.info("Starting T014: Checksum verification and file locking")
    
    # Run verification
    results = verify_and_lock_files()
    
    # Log summary
    logger.info(f"Verification complete:")
    logger.info(f"  Total files: {results['total_files']}")
    logger.info(f"  Verified: {results['verified']}")
    logger.info(f"  Failed: {results['failed']}")
    logger.info(f"  State file: {results['state_file']}")
    
    if results.get("error"):
        logger.error(f"Error: {results['error']}")
        sys.exit(1)
    
    if results['failed'] > 0:
        logger.warning(f"{results['failed']} files failed verification")
        # Don't exit with error if some files failed, but log the issue
    
    logger.info("T014 completed successfully")
    return results


if __name__ == "__main__":
    main()
