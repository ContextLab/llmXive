import os
import sys
import logging
import hashlib
from pathlib import Path
from utils import load_state, setup_logging

def compute_file_hash(file_path: str) -> str:
    """
    Compute the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If there is an error reading the file.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
            
    return sha256_hash.hexdigest()

def verify_artifacts() -> bool:
    """
    Verify that the SHA-256 hashes in state.yaml match the actual files.
    
    This function:
    1. Loads the state.yaml file.
    2. Iterates through all artifact entries in the state.
    3. Computes the current SHA-256 hash of each file.
    4. Compares the computed hash with the stored hash.
    5. Reports any mismatches or missing files.
    
    Returns:
        True if all artifacts match their recorded hashes.
        False if any mismatch or missing file is found.
    """
    logger = logging.getLogger(__name__)
    state_path = Path("state/state.yaml")
    
    if not state_path.exists():
        logger.error("State file not found: state/state.yaml")
        return False
        
    state = load_state(state_path)
    
    if not state or 'artifacts' not in state:
        logger.error("No artifacts found in state.yaml")
        return False
        
    all_match = True
    artifacts_checked = 0
    
    for artifact_name, artifact_info in state['artifacts'].items():
        if 'hash' not in artifact_info:
            logger.warning(f"Artifact '{artifact_name}' has no hash recorded in state.yaml")
            continue
            
        file_path = artifact_info.get('path')
        if not file_path:
            logger.warning(f"Artifact '{artifact_name}' has no path recorded in state.yaml")
            continue
            
        expected_hash = artifact_info['hash']
        full_path = Path(file_path)
        
        if not full_path.exists():
            logger.error(f"Artifact file missing: {file_path} (expected hash: {expected_hash})")
            all_match = False
            continue
            
        try:
            actual_hash = compute_file_hash(str(full_path))
            artifacts_checked += 1
            
            if actual_hash == expected_hash:
                logger.info(f"✓ Verified: {file_path}")
            else:
                logger.error(f"✗ Hash Mismatch: {file_path}")
                logger.error(f"  Expected: {expected_hash}")
                logger.error(f"  Actual:   {actual_hash}")
                all_match = False
                
        except Exception as e:
            logger.error(f"✗ Error computing hash for {file_path}: {e}")
            all_match = False
            
    if artifacts_checked == 0:
        logger.warning("No artifacts were successfully checked.")
        
    if all_match:
        logger.info(f"Artifact Integrity Check PASSED: {artifacts_checked} artifacts verified.")
    else:
        logger.error(f"Artifact Integrity Check FAILED: {artifacts_checked} artifacts checked.")
        
    return all_match

def main():
    """Main entry point for the artifact integrity check."""
    setup_logging("verify_artifacts")
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Artifact Integrity Check (T052)...")
    
    success = verify_artifacts()
    
    if success:
        logger.info("All artifacts match their recorded hashes.")
        sys.exit(0)
    else:
        logger.error("One or more artifacts failed the integrity check.")
        sys.exit(1)

if __name__ == "__main__":
    main()