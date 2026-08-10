import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logging import get_logger, error, info

logger = get_logger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied: {file_path}")

def scan_directory_for_hashes(
    directory: Path, extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Recursively scan a directory and calculate SHA-256 hashes for all files.
    
    Args:
        directory: The directory to scan.
        extensions: Optional list of file extensions to include (e.g., ['.py', '.yaml']).
                    If None, all files are included.
    
    Returns:
        A dictionary mapping relative file paths to their SHA-256 hashes.
    """
    hashes = {}
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return hashes
    
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            
            # Filter by extension if specified
            if extensions and file_path.suffix not in extensions:
                continue
            
            try:
                relative_path = file_path.relative_to(directory)
                file_hash = calculate_sha256(file_path)
                hashes[str(relative_path)] = file_hash
                logger.debug(f"Hashed: {relative_path}")
            except Exception as e:
                logger.error(f"Failed to hash {file_path}: {e}")
    
    return hashes

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Load an existing state file.
    
    Args:
        state_path: Path to the YAML state file.
    
    Returns:
        The loaded state dictionary, or an empty dict if the file doesn't exist.
    """
    if not state_path.exists():
        logger.info(f"State file not found, creating new: {state_path}")
        return {}
    
    try:
        with open(state_path, "r") as f:
            state = yaml.safe_load(f)
            return state if state else {}
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse state file {state_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Failed to load state file {state_path}: {e}")
        return {}

def save_state_file(state_path: Path, state: Dict[str, Any]) -> None:
    """
    Save the state dictionary to a YAML file.
    
    Args:
        state_path: Path to the output YAML state file.
        state: The state dictionary to save.
    """
    try:
        # Ensure parent directory exists
        state_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(state_path, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=True)
        logger.info(f"State file saved: {state_path}")
    except Exception as e:
        logger.error(f"Failed to save state file {state_path}: {e}")
        raise

def update_project_state(
    project_root: Path,
    state_path: Path,
    target_dirs: Optional[List[str]] = None,
    extensions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Update the project state file with SHA-256 hashes of all artifacts.
    
    Args:
        project_root: The root path of the project.
        state_path: The path to the state YAML file.
        target_dirs: Optional list of relative directory names to scan (e.g., ['code', 'data']).
                     If None, defaults to ['code', 'data', 'tests', 'artifacts'].
        extensions: Optional list of file extensions to include.
    
    Returns:
        The updated state dictionary.
    """
    if target_dirs is None:
        target_dirs = ['code', 'data', 'tests', 'analysis', 'models', 'training', 'utils']
    
    state = load_state_file(state_path)
    state['last_updated'] = datetime.now().isoformat()
    state['project_id'] = project_root.name
    state['artifacts'] = {}
    
    for dir_name in target_dirs:
        target_dir = project_root / dir_name
        if not target_dir.exists():
            logger.debug(f"Skipping non-existent directory: {target_dir}")
            continue
        
        logger.info(f"Scanning directory: {target_dir}")
        dir_hashes = scan_directory_for_hashes(target_dir, extensions)
        if dir_hashes:
            state['artifacts'][dir_name] = dir_hashes
    
    save_state_file(state_path, state)
    return state

def get_artifact_hash(
    artifact_path: Path,
    project_root: Path
) -> Optional[str]:
    """
    Get the SHA-256 hash of a specific artifact, either by calculating it
    or by looking it up in the state file.
    
    Args:
        artifact_path: Absolute path to the artifact.
        project_root: The root path of the project.
    
    Returns:
        The SHA-256 hash string, or None if not found/could not calculate.
    """
    if not artifact_path.exists():
        return None
    
    # Try to calculate it directly first
    try:
        return calculate_sha256(artifact_path)
    except Exception:
        return None

def main():
    """
    Main entry point for the state manager CLI.
    Updates the state file for the project.
    """
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Manage project state with SHA-256 hashes")
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Path to the project root directory"
    )
    parser.add_argument(
        "--state-file",
        type=str,
        default=None,
        help="Path to the state YAML file. If not provided, uses default location."
    )
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    
    if args.state_file:
        state_path = Path(args.state_file).resolve()
    else:
        # Default state file location as per task description
        state_path = project_root / "state" / f"{project_root.name}.yaml"
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"State file: {state_path}")
    
    try:
        state = update_project_state(project_root, state_path)
        logger.info("State update completed successfully.")
        print(f"State file updated: {state_path}")
        print(f"Artifacts tracked: {sum(len(v) for v in state.get('artifacts', {}).values())}")
    except Exception as e:
        logger.error(f"Failed to update state: {e}")
        raise

if __name__ == "__main__":
    main()
