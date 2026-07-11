"""
Artifact Hashing Module for llmXive Pipeline.

Implements Constitution Principle V: Reproducibility via Artifact Hashing.
Computes SHA256 hashes for all files in 'code/' and 'data/' directories
and updates the project state file (state/state.json) with these checksums.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import existing project utilities
from .logging import get_logger
from .config import get_paths

logger = get_logger(__name__)

# Directories to hash relative to project root
TARGET_DIRS = ['code', 'data']
STATE_FILE_NAME = 'state.json'
HASH_ALGORITHM = 'sha256'


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of a single file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise


def collect_files(directory: Path) -> List[Path]:
    """
    Recursively collect all files in a directory, excluding hidden files/dirs.

    Args:
        directory: Root directory to scan.

    Returns:
        List of Path objects for all regular files.
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []

    files = []
    for root, dirs, filenames in os.walk(directory):
        # Filter out hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for filename in filenames:
            if filename.startswith('.'):
                continue
            file_path = Path(root) / filename
            if file_path.is_file():
                files.append(file_path)
    
    return sorted(files)


def hash_directory(directory_name: str, project_root: Path) -> Dict[str, str]:
    """
    Compute hashes for all files in a specific directory.

    Args:
        directory_name: Name of the directory relative to project root.
        project_root: Root path of the project.

    Returns:
        Dictionary mapping relative file paths to their SHA256 hashes.
    """
    target_dir = project_root / directory_name
    file_hashes = {}
    
    files = collect_files(target_dir)
    logger.info(f"Hashing {len(files)} files in '{directory_name}/'...")
    
    for file_path in files:
        relative_path = file_path.relative_to(project_root)
        try:
            file_hash = compute_file_hash(file_path)
            file_hashes[str(relative_path)] = file_hash
        except Exception as e:
            logger.error(f"Skipping {relative_path} due to error: {e}")
            continue
    
    return file_hashes


def load_state(state_path: Path) -> Dict[str, Any]:
    """
    Load existing state file or return a new empty structure.

    Args:
        state_path: Path to the state.json file.

    Returns:
        Dictionary containing the state data.
    """
    if state_path.exists():
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read existing state file: {e}. Starting fresh.")
    
    return {
        "version": "1.0",
        "last_updated": None,
        "artifacts": {}
    }


def save_state(state: Dict[str, Any], state_path: Path) -> None:
    """
    Save the state dictionary to the JSON file.

    Args:
        state: The state dictionary to save.
        state_path: Path to the state.json file.
    """
    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, sort_keys=True)
    
    logger.info(f"State saved to {state_path}")


def update_state_with_hashes(state: Dict[str, Any], hashes: Dict[str, Dict[str, str]]) -> None:
    """
    Update the state dictionary with new artifact hashes.

    Args:
        state: The state dictionary to update (modified in place).
        hashes: Dictionary of directory names to file-hash mappings.
    """
    import datetime
    state["last_updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state["artifacts"] = hashes
    logger.info("State dictionary updated with new hashes.")


def main() -> int:
    """
    Main entry point for the hash_artifacts script.
    
    Returns:
        0 on success, 1 on failure.
    """
    logger.info("Starting artifact hashing process...")
    
    try:
        # Get project root from config
        paths = get_paths()
        project_root = paths.get('project_root', Path.cwd())
        
        if not isinstance(project_root, Path):
            project_root = Path(project_root)
        
        logger.info(f"Project root detected at: {project_root}")
        
        # Initialize state
        state_file = project_root / 'state' / STATE_FILE_NAME
        state = load_state(state_file)
        
        all_hashes = {}
        
        # Hash each target directory
        for dir_name in TARGET_DIRS:
            dir_hashes = hash_directory(dir_name, project_root)
            if dir_hashes:
                all_hashes[dir_name] = dir_hashes
            else:
                logger.warning(f"No files found to hash in '{dir_name}/'. Skipping.")
        
        if not all_hashes:
            logger.warning("No artifacts were hashed. Ensure 'code/' and 'data/' directories exist and contain files.")
            # We don't fail here, just update state with empty artifacts if needed
        
        # Update state
        update_state_with_hashes(state, all_hashes)
        
        # Save state
        save_state(state, state_file)
        
        logger.info("Artifact hashing completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error during hashing: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    # Initialize logging before running main
    # Assuming init_pipeline_logging is called elsewhere or we do it here for CLI usage
    from .logging import init_pipeline_logging
    init_pipeline_logging()
    
    sys.exit(main())
