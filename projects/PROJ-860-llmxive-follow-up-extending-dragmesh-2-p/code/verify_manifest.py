"""
Manifest verification script for DragMesh-2 dataset.

Computes SHA256 checksum of the fetched manifest, compares against expected
hash (if provided), and records the hash in both the project state file
and a local checksum file in the data/raw directory.

Implements Constitution Principle III: Data Integrity Verification.
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

from data_loader import fetch_dragmesh_manifest, get_manifest_checksum
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
CHECKSUM_FILE = DATA_RAW_DIR / ".checksums"

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


def load_expected_checksums() -> Dict[str, str]:
    """
    Load existing checksums from the local .checksums file.
    
    Returns:
        Dictionary mapping file names to their expected checksums
    """
    if not CHECKSUM_FILE.exists():
        return {}
    
    try:
        with open(CHECKSUM_FILE, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Could not load existing checksums: {e}")
        return {}


def save_local_checksums(checksums: Dict[str, str]) -> None:
    """
    Save checksums to the local .checksums file.
    
    Args:
        checksums: Dictionary mapping file names to checksums
    """
    with open(CHECKSUM_FILE, 'w') as f:
        yaml.dump(checksums, f, default_flow_style=False)
    logger.info(f"Saved checksums to {CHECKSUM_FILE}")


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
    state['updated_at'] = os.popen('date -u +"%Y-%m-%dT%H:%M:%SZ"').read().strip()
    
    save_state(STATE_FILE, state)
    logger.info(f"Updated state file {STATE_FILE} with manifest checksum")


def verify_manifest_integrity(expected_hash: Optional[str] = None) -> bool:
    """
    Verify the integrity of the DragMesh-2 manifest.
    
    Args:
        expected_hash: Optional expected hash to compare against
        
    Returns:
        True if verification passes, False otherwise
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
        raise FileNotFoundError(f"Manifest file not found at {manifest_path}")
    
    # Compute the checksum
    logger.info(f"Computing SHA256 for {manifest_path}...")
    manifest_hash = compute_file_sha256(manifest_path)
    logger.info(f"Manifest checksum: {manifest_hash}")
    
    # Compare against expected hash if provided
    if expected_hash and manifest_hash != expected_hash:
        logger.error(f"Checksum mismatch! Expected: {expected_hash}, Got: {manifest_hash}")
        return False
    
    # Save to local checksum file
    local_checksums = load_expected_checksums()
    local_checksums['dragmesh_manifest'] = manifest_hash
    save_local_checksums(local_checksums)
    
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
            logger.error("VERIFICATION FAILED: Checksum mismatch")
            return 1
    except Exception as e:
        logger.error(f"VERIFICATION FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
