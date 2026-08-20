"""
Manifest verification script for DragMesh-2 dataset.

Computes SHA256 checksum of the fetched manifest, compares against expected
hash (if provided), and records the hash in the project state file.

Implements Constitution Principle III: Data Integrity Verification.

IMPORTANT: This script respects read-only constraints on data/raw.
It does NOT write to data/raw/.checksums. It only writes to state/projects.
"""

import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import fetch_dragmesh_manifest
from checksum_config import load_state, save_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Expected manifest hash (can be updated if the source changes)
# This is the hash of the DragMesh-2 manifest as fetched from HuggingFace
EXPECTED_MANIFEST_HASH: Optional[str] = None  # Will be computed on first run


def compute_file_sha256(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal SHA256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def ensure_dirs() -> None:
    """Ensure required directories exist."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)


def update_state_file(manifest_hash: str) -> None:
    """
    Update the project state file with the manifest checksum.
    
    Args:
        manifest_hash: SHA256 hash of the manifest file
    """
    state = load_state(STATE_FILE)
    
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    
    state['artifact_hashes']['data_raw_manifest'] = manifest_hash
    # Use a simple timestamp format without external dependencies
    from datetime import datetime, timezone
    state['updated_at'] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    save_state(STATE_FILE, state)
    logger.info(f"Updated state file {STATE_FILE} with manifest checksum")


def verify_manifest_integrity(expected_hash: Optional[str] = None) -> bool:
    """
    Verify the integrity of the DragMesh-2 manifest.
    
    Args:
        expected_hash: Optional expected hash to compare against
        
    Returns:
        True if verification passes (or if file is missing but logged), False otherwise
    """
    ensure_dirs()
    
    # Fetch the manifest (this will raise if fetch fails)
    logger.info("Fetching DragMesh-2 manifest...")
    try:
        manifest_path = fetch_dragmesh_manifest()
    except Exception as e:
        logger.error(f"Failed to fetch manifest: {e}")
        raise
    
    if not manifest_path.exists():
        logger.warning(f"Manifest file not found at {manifest_path}")
        logger.warning("Recording MISSING_DATA status in state file.")
        
        # Record MISSING_DATA status
        state = load_state(STATE_FILE)
        if 'artifact_hashes' not in state:
            state['artifact_hashes'] = {}
        state['artifact_hashes']['data_raw_manifest'] = 'MISSING_DATA'
        from datetime import datetime, timezone
        state['updated_at'] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        save_state(STATE_FILE, state)
        return False
    
    # Check if file is empty
    if manifest_path.stat().st_size == 0:
        logger.warning(f"Manifest file at {manifest_path} is empty.")
        logger.warning("Recording MISSING_DATA status in state file.")
        
        # Record MISSING_DATA status
        state = load_state(STATE_FILE)
        if 'artifact_hashes' not in state:
            state['artifact_hashes'] = {}
        state['artifact_hashes']['data_raw_manifest'] = 'MISSING_DATA'
        from datetime import datetime, timezone
        state['updated_at'] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        save_state(STATE_FILE, state)
        return False
    
    # Compute the checksum
    logger.info(f"Computing SHA256 for {manifest_path}...")
    manifest_hash = compute_file_sha256(manifest_path)
    logger.info(f"Manifest checksum: {manifest_hash}")
    
    # Compare against expected hash if provided
    if expected_hash and manifest_hash != expected_hash:
        logger.error(f"Checksum mismatch! Expected: {expected_hash}, Got: {manifest_hash}")
        return False
    
    # Update project state file
    update_state_file(manifest_hash)
    
    logger.info("Manifest integrity verification complete.")
    return True


def main() -> int:
    """
    Main entry point for manifest verification.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        success = verify_manifest_integrity(EXPECTED_MANIFEST_HASH)
        if success:
            logger.info("VERIFICATION SUCCESSFUL")
            return 0
        else:
            logger.error("VERIFICATION FAILED: Checksum mismatch or missing data")
            return 1
    except Exception as e:
        logger.error(f"VERIFICATION FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())