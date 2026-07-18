"""
Hash checker module for llmXive pipeline.

Computes SHA256 hashes for all files in 'data/' and 'results/' directories
and updates the state tracking file in 'state/hash_state.yaml'.

Dependencies:
  - utils: compute_sha256, safe_join, setup_logging
  - config: load_config, get_path, ensure_dirs
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import datetime
import yaml

from utils import compute_sha256, safe_join, setup_logging
from config import load_config, get_path, ensure_dirs

def scan_directory(directory_path: Path) -> List[Path]:
    """
    Recursively scan a directory for all regular files.
    Ignores hidden files and directories (starting with '.').
    Returns a sorted list of file paths relative to the project root.
    """
    files = []
    if not directory_path.exists():
        logging.warning(f"Directory does not exist: {directory_path}")
        return files

    for root, dirs, filenames in os.walk(directory_path):
        # Filter out hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for filename in filenames:
            if filename.startswith('.'):
                continue
            
            full_path = Path(root) / filename
            files.append(full_path)
    
    return sorted(files)

def compute_hashes_for_directory(directory_name: str) -> Dict[str, str]:
    """
    Compute SHA256 hashes for all files in a specific directory.
    
    Args:
        directory_name: Name of the directory (e.g., 'data', 'results')
        
    Returns:
        Dictionary mapping relative file paths to their SHA256 hashes.
    """
    base_path = get_path(directory_name)
    files = scan_directory(base_path)
    
    hashes = {}
    for file_path in files:
        try:
            # Compute hash relative to project root
            rel_path = file_path.relative_to(Path.cwd())
            hash_value = compute_sha256(file_path)
            hashes[str(rel_path)] = hash_value
            logging.debug(f"Hashed: {rel_path}")
        except Exception as e:
            logging.error(f"Failed to hash {file_path}: {e}")
            
    return hashes

def load_current_state(state_path: Path) -> Dict[str, Any]:
    """Load existing state file if it exists, otherwise return empty structure."""
    if state_path.exists():
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logging.warning(f"Could not parse existing state file: {e}. Starting fresh.")
            return {}
    return {}

def save_state(state: Dict[str, Any], state_path: Path) -> None:
    """Save the state dictionary to the YAML file."""
    # Ensure state directory exists
    ensure_dirs(state_path.parent)
    
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=True)
    logging.info(f"State saved to {state_path}")

def update_hash_state() -> None:
    """
    Main entry point: Scan 'data/' and 'results/', compute hashes,
    and update the state YAML file.
    """
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting hash computation for data and results directories.")
    
    # Load config to ensure paths are valid
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return

    # Define directories to hash
    target_dirs = ['data', 'results']
    
    # Initialize state structure
    state_path = get_path('state/hash_state.yaml')
    state = load_current_state(state_path)
    
    # Ensure state directory exists
    ensure_dirs(Path('state'))
    
    state_updated = False
    
    for dir_name in target_dirs:
        dir_path = get_path(dir_name)
        if not dir_path.exists():
            logger.info(f"Skipping {dir_name}: directory does not exist.")
            # Initialize empty entry if missing
            if dir_name not in state:
                state[dir_name] = {}
                state_updated = True
            continue
        
        logger.info(f"Scanning {dir_name} directory...")
        new_hashes = compute_hashes_for_directory(dir_name)
        
        old_hashes = state.get(dir_name, {})
        
        # Check if anything changed
        if old_hashes != new_hashes:
            state[dir_name] = new_hashes
            state_updated = True
            logger.info(f"Updated hashes for {dir_name} ({len(new_hashes)} files).")
        else:
            logger.info(f"No changes detected in {dir_name}.")
    
    # Update timestamp if any changes occurred or if state is new
    if state_updated or 'last_updated' not in state:
        state['last_updated'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        state_updated = True
    
    if state_updated:
        save_state(state, state_path)
        logger.info("Hash state update completed successfully.")
    else:
        logger.info("No changes to save.")

if __name__ == "__main__":
    update_hash_state()
