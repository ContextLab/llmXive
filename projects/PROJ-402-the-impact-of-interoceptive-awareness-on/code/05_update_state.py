import hashlib
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
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
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def scan_directory_for_artifacts(directory: Path) -> list:
    """
    Recursively scan a directory for all files.
    
    Args:
        directory: Path to the directory to scan.
        
    Returns:
        List of Path objects for all files found.
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []
    
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = Path(root) / filename
            # Skip hidden files and common temporary files
            if not filename.startswith('.') and not filename.endswith('~'):
                files.append(file_path)
    return files

def load_state_file(state_path: Path) -> dict:
    """
    Load the state YAML file.
    
    Args:
        state_path: Path to the state file.
        
    Returns:
        Dictionary containing the state data.
    """
    if not state_path.exists():
        logger.info(f"State file not found, initializing new state: {state_path}")
        return {
            "project_id": "PROJ-402-the-impact-of-interoceptive-awareness-on",
            "last_updated": None,
            "artifact_hashes": {}
        }
    
    try:
        with open(state_path, "r") as f:
            state = yaml.safe_load(f)
            if state is None:
                state = {
                    "project_id": "PROJ-402-the-impact-of-interoceptive-awareness-on",
                    "last_updated": None,
                    "artifact_hashes": {}
                }
            return state
    except yaml.YAMLError as e:
        logger.error(f"Error parsing state file {state_path}: {e}")
        raise

def update_state_file(state_path: Path, state: dict) -> None:
    """
    Update the state YAML file with new data.
    
    Args:
        state_path: Path to the state file.
        state: Dictionary containing the updated state data.
    """
    state["last_updated"] = datetime.now().isoformat()
    
    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(state_path, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State file updated successfully: {state_path}")
    except IOError as e:
        logger.error(f"Error writing state file {state_path}: {e}")
        raise

def compute_artifact_hashes(data_dir: Path, state_path: Path) -> dict:
    """
    Compute hashes for all files under the data directory and update state.
    
    This function scans the data directory (including derived artifacts),
    computes SHA-256 hashes for every file, and updates the state file
    with the new hash map.
    
    Args:
        data_dir: Path to the data directory (e.g., 'data/').
        state_path: Path to the state YAML file.
        
    Returns:
        Dictionary containing the updated artifact hashes.
    """
    logger.info(f"Starting artifact hash computation for directory: {data_dir}")
    
    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        # Initialize empty hashes if directory missing
        artifact_hashes = {}
    else:
        files = scan_directory_for_artifacts(data_dir)
        logger.info(f"Found {len(files)} files in {data_dir}")
        
        artifact_hashes = {}
        for file_path in files:
            try:
                # Store relative path from data_dir for cleaner state file
                rel_path = file_path.relative_to(data_dir)
                file_hash = compute_sha256(file_path)
                artifact_hashes[str(rel_path)] = file_hash
                logger.debug(f"Hashed: {rel_path} -> {file_hash[:16]}...")
            except Exception as e:
                logger.error(f"Failed to hash file {file_path}: {e}")
                # Continue processing other files
    
    # Load current state
    state = load_state_file(state_path)
    
    # Update artifact hashes in state
    state["artifact_hashes"] = artifact_hashes
    
    # Write updated state
    update_state_file(state_path, state)
    
    logger.info(f"Completed hash computation. Total artifacts: {len(artifact_hashes)}")
    return artifact_hashes

def main():
    """
    Main entry point for the state update script.
    
    Computes SHA-256 hashes for all files under 'data/' (including
    derived artifacts like data/derived/hrv_metrics.csv) and updates
    the state file at 'state/projects/001-impact-of-interoceptive-awareness.yaml'.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    state_dir = project_root / "state" / "projects"
    state_file = state_dir / "001-impact-of-interoceptive-awareness.yaml"
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"State file: {state_file}")
    
    # Ensure state directory exists
    state_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        hashes = compute_artifact_hashes(data_dir, state_file)
        
        # Summary output
        logger.info("Artifact Hash Summary:")
        for rel_path, file_hash in sorted(hashes.items()):
            logger.info(f"  {rel_path}: {file_hash[:32]}...")
        
        print(f"SUCCESS: Updated state file with {len(hashes)} artifact hashes.")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Failed to update state: {e}")
        print(f"ERROR: Failed to update state: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()