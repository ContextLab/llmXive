import os
import sys
import json
import hashlib
import logging
from pathlib import Path

from state_manager import load_artifacts_state, compute_sha256

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_sha256_file(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return None

def load_artifacts_state(state_path: str = None) -> dict:
    """Load the artifacts state from YAML."""
    if state_path is None:
        state_path = Path("state/artifacts.yaml")
    else:
        state_path = Path(state_path)
    
    if not state_path.exists():
        logger.error(f"State file not found: {state_path}")
        return {}
    
    try:
        import yaml
        with open(state_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Error loading state file: {e}")
        return {}

def validate_artifact_entry(entry: dict, base_path: str = "") -> bool:
    """
    Validate a single artifact entry in the state.
    Returns True if the file exists and the hash matches.
    """
    file_path = Path(base_path) / entry.get("path", "")
    expected_hash = entry.get("sha256")
    
    if not file_path.exists():
        logger.error(f"Artifact missing: {file_path}")
        return False
    
    if not expected_hash:
        logger.warning(f"No hash recorded for: {file_path}")
        return False
    
    actual_hash = compute_sha256_file(str(file_path))
    
    if actual_hash != expected_hash:
        logger.error(f"Hash mismatch for {file_path}: expected {expected_hash}, got {actual_hash}")
        return False
    
    logger.info(f"Verified: {file_path} (SHA-256: {actual_hash[:16]}...)")
    return True

def main():
    project_root = Path(__file__).parent.parent
    state_path = project_root / "state" / "artifacts.yaml"
    
    if not state_path.exists():
        logger.error(f"State file not found at {state_path}. Task T033 cannot be completed.")
        sys.exit(1)
    
    logger.info(f"Loading state from {state_path}...")
    state = load_artifacts_state(str(state_path))
    
    if not state:
        logger.warning("State file is empty or invalid.")
        sys.exit(0)
    
    artifacts = state.get("artifacts", {})
    if not artifacts:
        logger.warning("No artifacts found in state file.")
        sys.exit(0)
    
    logger.info(f"Found {len(artifacts)} artifacts to verify.")
    
    all_valid = True
    for name, entry in artifacts.items():
        if not isinstance(entry, dict):
            logger.error(f"Invalid entry format for artifact: {name}")
            all_valid = False
            continue
        
        if not validate_artifact_entry(entry, base_path=str(project_root)):
            all_valid = False
    
    if all_valid:
        logger.info("SUCCESS: All artifacts in state/artifacts.yaml are present and checksummed correctly.")
        sys.exit(0)
    else:
        logger.error("FAILURE: Some artifacts are missing or have mismatched checksums.")
        sys.exit(1)

if __name__ == "__main__":
    main()