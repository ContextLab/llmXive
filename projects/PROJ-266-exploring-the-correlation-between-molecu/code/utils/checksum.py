"""
Checksum utility for generating and registering SHA-256 checksums for data files.

This module provides functions to compute SHA-256 checksums for files in the data/
directory and update the project state file with the new hashes.

Usage:
    python code/utils/checksum.py
"""
import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml

# Import from sibling modules
from utils.config import get_project_root, get_state_path
from utils.logging import get_logger, configure_root_logger

# Constants
CHECKSUM_ALGORITHM = "sha256"
STATE_FILE_PATH = "state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml"
DATA_DIR = "data"

def get_logger_for_module() -> logging.Logger:
    """Get a logger configured for this module."""
    return get_logger(__name__)

def compute_file_checksum(file_path: Path, algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to compute checksum for.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal string of the checksum.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    logger = get_logger_for_module()
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    if algorithm != CHECKSUM_ALGORITHM:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Only {CHECKSUM_ALGORITHM} is supported.")
        
    logger.debug(f"Computing checksum for {file_path}")
    
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_obj.update(chunk)
            
    return hash_obj.hexdigest()

def load_state_file(state_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the project state file.
    
    Args:
        state_path: Path to the state file. If None, uses the default path.
        
    Returns:
        Dictionary containing the state file contents.
        
    Raises:
        FileNotFoundError: If the state file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    logger = get_logger_for_module()
    
    if state_path is None:
        state_path = get_project_root() / STATE_FILE_PATH
        
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")
        
    logger.debug(f"Loading state file from {state_path}")
    
    with open(state_path, 'r') as f:
        state = yaml.safe_load(f)
        
    if state is None:
        state = {}
        
    return state

def save_state_file(state: Dict[str, Any], state_path: Optional[Path] = None) -> None:
    """
    Save the project state file.
    
    Args:
        state: Dictionary to save.
        state_path: Path to the state file. If None, uses the default path.
        
    Raises:
        IOError: If the file cannot be written.
    """
    logger = get_logger_for_module()
    
    if state_path is None:
        state_path = get_project_root() / STATE_FILE_PATH
        
    # Ensure parent directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.debug(f"Saving state file to {state_path}")
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def register_checksum(file_path: Path, state: Dict[str, Any], checksum: Optional[str] = None) -> Dict[str, Any]:
    """
    Register a file checksum in the state file.
    
    Args:
        file_path: Path to the file.
        state: Current state dictionary.
        checksum: Pre-computed checksum. If None, will be computed.
        
    Returns:
        Updated state dictionary.
    """
    logger = get_logger_for_module()
    
    if checksum is None:
        checksum = compute_file_checksum(file_path)
        
    # Normalize file path to be relative to project root
    project_root = get_project_root()
    try:
        relative_path = file_path.relative_to(project_root)
    except ValueError:
        relative_path = file_path  # Fallback to absolute path if not relative
        
    # Ensure checksums section exists
    if 'checksums' not in state:
        state['checksums'] = {}
        
    # Update checksum
    state['checksums'][str(relative_path)] = {
        'algorithm': CHECKSUM_ALGORITHM,
        'hash': checksum,
        'registered_at': None  # Could be populated with timestamp if needed
    }
    
    logger.info(f"Registered checksum for {relative_path}: {checksum[:16]}...")
    
    return state

def scan_and_register_data_files(data_dir: Optional[Path] = None) -> List[str]:
    """
    Scan the data directory for files and register their checksums.
    
    Args:
        data_dir: Path to the data directory. If None, uses the default path.
        
    Returns:
        List of registered file paths.
    """
    logger = get_logger_for_module()
    
    if data_dir is None:
        data_dir = get_project_root() / DATA_DIR
        
    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        return []
        
    # Load current state
    try:
        state = load_state_file()
    except FileNotFoundError:
        logger.warning(f"State file not found. Creating new state file.")
        state = {}
        
    registered_files = []
    
    # Walk through data directory
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            file_path = Path(root) / file
            
            # Skip hidden files and common non-data files
            if file.startswith('.') or file.endswith(('.py', '.pyc', '.md', '.txt', '.yaml', '.yml')):
                continue
                
            try:
                checksum = compute_file_checksum(file_path)
                state = register_checksum(file_path, state, checksum)
                registered_files.append(str(file_path.relative_to(get_project_root())))
            except Exception as e:
                logger.error(f"Failed to compute checksum for {file_path}: {e}")
                
    # Save updated state
    save_state_file(state)
    
    logger.info(f"Registered checksums for {len(registered_files)} files.")
    
    return registered_files

def verify_checksum(file_path: Path, expected_checksum: str, state: Optional[Dict[str, Any]] = None) -> bool:
    """
    Verify a file's checksum against an expected value.
    
    Args:
        file_path: Path to the file.
        expected_checksum: Expected checksum value.
        state: State dictionary containing registered checksums. If None, will be loaded.
        
    Returns:
        True if checksum matches, False otherwise.
    """
    logger = get_logger_for_module()
    
    if state is None:
        try:
            state = load_state_file()
        except FileNotFoundError:
            logger.warning("State file not found. Cannot verify checksum.")
            return False
            
    actual_checksum = compute_file_checksum(file_path)
    
    if actual_checksum == expected_checksum:
        logger.info(f"Checksum verified for {file_path}")
        return True
    else:
        logger.error(f"Checksum mismatch for {file_path}: expected {expected_checksum}, got {actual_checksum}")
        return False

def main() -> int:
    """
    Main entry point for the checksum utility.
    
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    configure_root_logger()
    logger = get_logger_for_module()
    
    try:
        logger.info("Starting checksum utility")
        
        # Scan and register all data files
        registered_files = scan_and_register_data_files()
        
        if registered_files:
            logger.info(f"Successfully registered {len(registered_files)} files:")
            for f in registered_files:
                logger.info(f"  - {f}")
        else:
            logger.warning("No files were registered. Check if data directory is empty or contains only skipped files.")
            
        return 0
        
    except Exception as e:
        logger.error(f"Checksum utility failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
