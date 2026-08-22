import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def scan_directory_for_artifacts(base_dir: Path, pattern: Optional[str] = None) -> List[Path]:
    """
    Scan a directory for files matching a pattern.
    
    Args:
        base_dir: Root directory to scan.
        pattern: Optional glob pattern (e.g., "*.csv", "*.parquet"). 
                 If None, returns all files.
                
    Returns:
        List of Path objects for matching files.
    """
    if not base_dir.exists():
        logger.warning(f"Directory does not exist: {base_dir}")
        return []
    
    if pattern:
        return list(base_dir.rglob(pattern))
    else:
        return [p for p in base_dir.rglob('*') if p.is_file()]

def load_state(state_path: Path) -> Dict[str, Any]:
    """
    Load the state YAML file.
    
    Args:
        state_path: Path to the state YAML file.
        
    Returns:
        Dictionary containing the state, or empty dict if file missing.
    """
    if not state_path.exists():
        logger.info(f"State file not found at {state_path}, initializing empty state.")
        return {"project_id": None, "artifacts": {}}
    
    try:
        with open(state_path, "r") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing state file {state_path}: {e}")
        raise

def save_state(state: Dict[str, Any], state_path: Path) -> None:
    """
    Save the state dictionary to a YAML file.
    
    Args:
        state: Dictionary to save.
        state_path: Path to the state YAML file.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(state_path, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State saved to {state_path}")
    except IOError as e:
        logger.error(f"Error writing state file {state_path}: {e}")
        raise

def update_artifact_hashes(
    state: Dict[str, Any], 
    project_id: str, 
    data_dirs: List[Path]
) -> Dict[str, Any]:
    """
    Scan specified data directories, compute hashes, and update the state dictionary.
    
    Args:
        state: Current state dictionary.
        project_id: Project identifier (e.g., "PROJ-006-agriculture-optimization").
        data_dirs: List of directories to scan for artifacts (e.g., data/raw, data/processed).
        
    Returns:
        Updated state dictionary.
    """
    state["project_id"] = project_id
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    for directory in data_dirs:
        dir_str = str(directory.relative_to(Path.cwd())) if directory.is_absolute() else str(directory)
        logger.info(f"Scanning directory: {dir_str}")
        
        files = scan_directory_for_artifacts(directory)
        dir_hashes = {}
        
        for file_path in files:
            try:
                rel_path = str(file_path.relative_to(Path.cwd()))
                file_hash = compute_file_hash(file_path)
                dir_hashes[rel_path] = file_hash
                logger.debug(f"Hashed {rel_path}: {file_hash}")
            except (FileNotFoundError, IOError) as e:
                logger.warning(f"Skipping {file_path} due to error: {e}")
        
        state["artifacts"][dir_str] = {
            "last_updated": None, # Can be populated with datetime if needed
            "files": dir_hashes
        }
    
    return state

def verify_artifacts(state: Dict[str, Any], project_id: str) -> bool:
    """
    Verify that the current file hashes match those stored in the state.
    
    Args:
        state: The loaded state dictionary.
        project_id: The expected project ID.
        
    Returns:
        True if all artifacts match, False otherwise.
    """
    if state.get("project_id") != project_id:
        logger.warning(f"Project ID mismatch: expected {project_id}, got {state.get('project_id')}")
        return False
    
    artifacts = state.get("artifacts", {})
    if not artifacts:
        logger.warning("No artifacts found in state.")
        return False
    
    all_match = True
    for dir_name, dir_info in artifacts.items():
        dir_path = Path(dir_name)
        if not dir_path.exists():
            logger.warning(f"Directory missing: {dir_name}")
            all_match = False
            continue
        
        stored_files = dir_info.get("files", {})
        current_files = {str(p.relative_to(Path.cwd())): p for p in dir_path.rglob('*') if p.is_file()}
        
        # Check for missing or new files
        stored_paths = set(stored_files.keys())
        current_paths = set(current_files.keys())
        
        if stored_paths != current_paths:
            logger.warning(f"File set mismatch in {dir_name}: stored={stored_paths}, current={current_paths}")
            all_match = False
            continue
        
        # Check hashes
        for rel_path, stored_hash in stored_files.items():
            file_path = current_files[rel_path]
            try:
                current_hash = compute_file_hash(file_path)
                if current_hash != stored_hash:
                    logger.warning(f"Hash mismatch for {rel_path}: stored={stored_hash}, current={current_hash}")
                    all_match = False
            except (FileNotFoundError, IOError) as e:
                logger.warning(f"Error reading {rel_path} for verification: {e}")
                all_match = False
    
    return all_match

def main():
    """
    CLI entry point for state management.
    Usage: python -m src.utils.state_manager --project-id PROJ-006 --scan data/raw data/processed
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage project state and artifact hashes.")
    parser.add_argument("--project-id", type=str, required=True, help="Project ID (e.g., PROJ-006-agriculture-optimization)")
    parser.add_argument("--scan", nargs='+', type=str, required=True, help="Directories to scan (e.g., data/raw data/processed)")
    parser.add_argument("--verify", action="store_true", help="Verify existing hashes against current files")
    parser.add_argument("--state-path", type=str, default="state/projects/PROJ-006-agriculture-optimization.yaml", help="Path to state file")
    
    args = parser.parse_args()
    
    state_path = Path(args.state_path)
    data_dirs = [Path(d) for d in args.scan]
    
    # Ensure state path directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    state = load_state(state_path)
    
    if args.verify:
        logger.info(f"Verifying artifacts for project {args.project_id}...")
        is_valid = verify_artifacts(state, args.project_id)
        if is_valid:
            logger.info("Verification successful: All artifacts match.")
        else:
            logger.warning("Verification failed: Artifacts do not match or are missing.")
    else:
        logger.info(f"Updating artifact hashes for project {args.project_id}...")
        state = update_artifact_hashes(state, args.project_id, data_dirs)
        save_state(state, state_path)
        logger.info("State update complete.")

if __name__ == "__main__":
    main()
