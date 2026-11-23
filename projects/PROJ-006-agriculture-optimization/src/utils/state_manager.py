import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

# Configure logging for the module
logger = logging.getLogger(__name__)

PROJECT_STATE_PATH = Path("state/projects/PROJ-006-agriculture-optimization.yaml")
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def scan_directory_for_artifacts(base_dir: Path) -> List[Path]:
    """
    Recursively scan a directory for all files.
    
    Args:
        base_dir: Root directory to scan.
        
    Returns:
        List of Path objects for all files found.
    """
    if not base_dir.exists():
        logger.warning(f"Directory does not exist: {base_dir}")
        return []
    
    artifacts = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            artifacts.append(Path(root) / file)
    return artifacts

def load_state(state_path: Path) -> Dict[str, Any]:
    """
    Load the state YAML file.
    
    Args:
        state_path: Path to the state file.
        
    Returns:
        Dictionary containing the state. If file doesn't exist, returns empty structure.
    """
    if not state_path.exists():
        logger.info(f"State file not found, initializing new state at {state_path}")
        return {
            "project_id": "PROJ-006-agriculture-optimization",
            "artifact_hashes": {
                "data_raw": {},
                "data_processed": {}
            }
        }
    
    try:
        with open(state_path, "r") as f:
            state = yaml.safe_load(f)
            # Ensure structure exists if file was empty or malformed
            if "artifact_hashes" not in state:
                state["artifact_hashes"] = {"data_raw": {}, "data_processed": {}}
            return state
    except yaml.YAMLError as e:
        logger.error(f"Error parsing state file {state_path}: {e}")
        return {
            "project_id": "PROJ-006-agriculture-optimization",
            "artifact_hashes": {
                "data_raw": {},
                "data_processed": {}
            }
        }

def save_state(state: Dict[str, Any], state_path: Path) -> None:
    """
    Save the state dictionary to the YAML file.
    
    Args:
        state: Dictionary to save.
        state_path: Path to the state file.
    """
    # Ensure parent directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)
    logger.info(f"State saved to {state_path}")

def update_artifact_hashes(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scan data directories and update hashes in the state.
    
    Args:
        state: Current state dictionary.
        
    Returns:
        Updated state dictionary.
    """
    # Scan data/raw
    raw_files = scan_directory_for_artifacts(DATA_RAW_DIR)
    raw_hashes = {}
    for file_path in raw_files:
        try:
            file_hash = compute_file_hash(file_path)
            # Store relative path from data/raw
            rel_path = str(file_path.relative_to(DATA_RAW_DIR))
            raw_hashes[rel_path] = file_hash
        except (FileNotFoundError, IOError) as e:
            logger.warning(f"Skipping {file_path}: {e}")
    
    if not raw_hashes:
        logger.info("No data to hash in data/raw")
    
    # Scan data/processed
    processed_files = scan_directory_for_artifacts(DATA_PROCESSED_DIR)
    processed_hashes = {}
    for file_path in processed_files:
        try:
            file_hash = compute_file_hash(file_path)
            # Store relative path from data/processed
            rel_path = str(file_path.relative_to(DATA_PROCESSED_DIR))
            processed_hashes[rel_path] = file_hash
        except (FileNotFoundError, IOError) as e:
            logger.warning(f"Skipping {file_path}: {e}")
    
    if not processed_hashes:
        logger.info("No data to hash in data/processed")
    
    state["artifact_hashes"]["data_raw"] = raw_hashes
    state["artifact_hashes"]["data_processed"] = processed_hashes
    return state

def verify_artifacts(state: Dict[str, Any]) -> bool:
    """
    Verify that all recorded artifacts still exist and match their hashes.
    
    Args:
        state: State dictionary containing artifact hashes.
        
    Returns:
        True if all artifacts are valid, False otherwise.
    """
    all_valid = True
    
    # Check data/raw
    for rel_path, expected_hash in state["artifact_hashes"]["data_raw"].items():
        full_path = DATA_RAW_DIR / rel_path
        if not full_path.exists():
            logger.error(f"Artifact missing: {full_path}")
            all_valid = False
            continue
        
        try:
            current_hash = compute_file_hash(full_path)
            if current_hash != expected_hash:
                logger.error(f"Hash mismatch for {full_path}: expected {expected_hash}, got {current_hash}")
                all_valid = False
        except (FileNotFoundError, IOError) as e:
            logger.error(f"Error verifying {full_path}: {e}")
            all_valid = False
    
    # Check data/processed
    for rel_path, expected_hash in state["artifact_hashes"]["data_processed"].items():
        full_path = DATA_PROCESSED_DIR / rel_path
        if not full_path.exists():
            logger.error(f"Artifact missing: {full_path}")
            all_valid = False
            continue
        
        try:
            current_hash = compute_file_hash(full_path)
            if current_hash != expected_hash:
                logger.error(f"Hash mismatch for {full_path}: expected {expected_hash}, got {current_hash}")
                all_valid = False
        except (FileNotFoundError, IOError) as e:
            logger.error(f"Error verifying {full_path}: {e}")
            all_valid = False
    
    return all_valid

def main() -> int:
    """
    Main entry point for CLI usage.
    
    Performs:
    1. Load existing state (or initialize if missing).
    2. Scan data directories and update hashes.
    3. Save updated state.
    4. Verify artifacts (optional dry-run check).
    
    Returns:
        0 on success, 1 on failure.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    logger.info("Starting state manager update...")
    
    # Load or initialize state
    state = load_state(PROJECT_STATE_PATH)
    
    # Update hashes
    state = update_artifact_hashes(state)
    
    # Save state
    save_state(state, PROJECT_STATE_PATH)
    
    # Verify
    if verify_artifacts(state):
        logger.info("All artifacts verified successfully.")
        return 0
    else:
        logger.error("Artifact verification failed.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
