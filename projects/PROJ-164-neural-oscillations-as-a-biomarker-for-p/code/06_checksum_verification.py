import os
import stat
import sys
import logging
from pathlib import Path
from utils.io_helpers import compute_sha256, write_checksum_to_state

def set_read_only(file_path: Path) -> None:
    """
    Set file permissions to read-only (chmod 444).
    Raises PermissionError if the operation fails.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        # Read-only for owner, group, others (r--r--r--)
        os.chmod(file_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        logging.info(f"Set read-only permissions on: {file_path}")
    except PermissionError as e:
        logging.error(f"Failed to set read-only permissions on {file_path}: {e}")
        raise

def verify_and_lock_files(raw_dir: Path, project_id: str) -> bool:
    """
    Verify SHA-256 checksums for all files in the raw data directory.
    If verification passes, set files to read-only and log results to state.
    
    Args:
        raw_dir: Path to the raw data directory (e.g., data/raw)
        project_id: Project identifier for state file naming
        
    Returns:
        True if all files verified successfully and locked, False otherwise.
    """
    if not raw_dir.exists():
        logging.error(f"Raw data directory does not exist: {raw_dir}")
        return False
    
    # Get all files in the directory (non-recursive for safety)
    files = [f for f in raw_dir.iterdir() if f.is_file()]
    
    if not files:
        logging.warning(f"No files found in {raw_dir} to verify.")
        return True  # No files to verify, considered success
    
    all_verified = True
    checksums = {}
    
    for file_path in files:
        logging.info(f"Verifying checksum for: {file_path.name}")
        try:
            checksum = compute_sha256(file_path)
            checksums[file_path.name] = checksum
            
            # Set to read-only immediately after successful verification
            set_read_only(file_path)
            
        except Exception as e:
            logging.error(f"Verification failed for {file_path.name}: {e}")
            all_verified = False
    
    if all_verified and checksums:
        # Write checksums to state file
        state_file = write_checksum_to_state(project_id, checksums)
        if state_file:
            logging.info(f"All checksums verified and written to: {state_file}")
        else:
            logging.error("Failed to write checksums to state file.")
            all_verified = False
    elif not checksums:
        logging.warning("No files were successfully verified.")
        
    return all_verified

def main():
    """
    Main entry point for checksum verification task (T014).
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/pipeline.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting T014: Checksum verification and locking.")
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / "data" / "raw"
    project_id = "PROJ-164-neural-oscillations-as-a-biomarker-for-p"
    
    # Execute verification
    success = verify_and_lock_files(raw_dir, project_id)
    
    if success:
        logger.info("T014 completed successfully.")
        sys.exit(0)
    else:
        logger.error("T014 failed: Checksum verification or locking failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
