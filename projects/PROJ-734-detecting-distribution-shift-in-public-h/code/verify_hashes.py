import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Import logging setup to ensure consistent logging format
try:
    from logging_setup import setup_logging
except ImportError:
    # Fallback if logging_setup is not available yet in execution context
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        raise

def verify_and_update_hashes(state_file: str = "state/hashes.json", data_dir: str = "data") -> bool:
    """
    Verify all files in data/ have SHA256 hashes and update state/hashes.json.
    
    Returns True if all verifications pass and state is updated.
    Returns False if verification fails or state cannot be updated.
    """
    logger.info(f"Starting hash verification for {data_dir}")
    
    # Ensure state directory exists
    state_dir = Path("state")
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing state if it exists
    existing_hashes = {}
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                existing_hashes = json.load(f)
            logger.info(f"Loaded existing state from {state_file}")
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Could not load existing state: {e}. Starting fresh.")
            existing_hashes = {}
    
    # Find all files in data directory
    data_path = Path(data_dir)
    if not data_path.exists():
        logger.error(f"Data directory {data_dir} does not exist")
        return False
    
    files_to_check = list(data_path.rglob("*"))
    files_to_check = [f for f in files_to_check if f.is_file()]
    
    if not files_to_check:
        logger.warning(f"No files found in {data_dir}")
        return True  # No files to verify is technically success
    
    new_hashes = {}
    all_verified = True
    
    for file_path in files_to_check:
        relative_path = str(file_path.relative_to(Path(".")))
        logger.info(f"Verifying: {relative_path}")
        
        try:
            current_hash = calculate_sha256(str(file_path))
            new_hashes[relative_path] = current_hash
            
            # Check against existing hash if available
            if relative_path in existing_hashes:
                if existing_hashes[relative_path] == current_hash:
                    logger.info(f"  ✓ Hash verified: {relative_path}")
                else:
                    logger.warning(f"  ⚠ Hash mismatch for {relative_path}")
                    logger.warning(f"    Expected: {existing_hashes[relative_path]}")
                    logger.warning(f"    Found:    {current_hash}")
                    all_verified = False
            else:
                logger.info(f"  ℹ New file detected: {relative_path}")
                
        except Exception as e:
            logger.error(f"  ✗ Failed to verify {relative_path}: {e}")
            all_verified = False
    
    # Update state file
    try:
        with open(state_file, 'w') as f:
            json.dump(new_hashes, f, indent=2, sort_keys=True)
        logger.info(f"Updated state file: {state_file}")
    except Exception as e:
        logger.error(f"Failed to update state file: {e}")
        return False
    
    if all_verified:
        logger.info("All file hashes verified successfully")
    else:
        logger.warning("Some files had hash mismatches or verification errors")
        
    return all_verified

def main():
    """Main entry point for hash verification."""
    setup_logging()
    logger.info("=== Distribution Shift Detection - Hash Verification ===")
    
    success = verify_and_update_hashes()
    
    if success:
        logger.info("Verification completed successfully")
        return 0
    else:
        logger.error("Verification completed with errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())
