import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import pandas as pd
import yaml

from utils.logger import get_logger, log_execution_start, log_execution_end
from data.config import get_config

logger = get_logger(__name__)

def calculate_file_hash(file_path: Union[str, Path]) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path} for hashing: {e}")
        raise

def load_data_to_raw(
    source_path: Union[str, Path],
    target_dir: Optional[Union[str, Path]] = None
) -> Path:
    """
    Copy or move a data file (CSV) to the data/raw directory.
    If the source is already in data/raw, it verifies existence.
    If the source is from download.py (synthetic or real), it copies it.
    
    Args:
        source_path: Path to the source data file (CSV).
        target_dir: Optional target directory. Defaults to project's data/raw.
        
    Returns:
        Path to the file in data/raw.
        
    Raises:
        FileNotFoundError: If source file does not exist.
        ValueError: If file extension is not .csv.
    """
    source_path = Path(source_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Source data file not found: {source_path}")
    
    if source_path.suffix.lower() != '.csv':
        raise ValueError(f"Expected CSV file, got: {source_path.suffix}")
    
    config = get_config()
    target_dir = Path(target_dir) if target_dir else config.data_raw_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    
    target_path = target_dir / source_path.name
    
    # Copy the file to data/raw
    import shutil
    shutil.copy2(source_path, target_path)
    logger.info(f"Copied data to raw: {target_path}")
    
    return target_path

def write_artifact_hashes_to_state(
    file_paths: list,
    state_key: str = "artifact_hashes"
) -> None:
    """
    Calculate SHA-256 hashes for a list of files and write them to the project state YAML.
    
    Args:
        file_paths: List of file paths to hash.
        state_key: The key in the state YAML where hashes will be stored.
        
    Raises:
        FileNotFoundError: If any file in the list does not exist.
        IOError: If the state file cannot be read or written.
    """
    config = get_config()
    state_file = config.state_project_file
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or initialize
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing state file {state_file}: {e}")
            raise
    else:
        state_data = {}
    
    if state_key not in state_data:
        state_data[state_key] = {}
    
    hashes = {}
    for path in file_paths:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Cannot hash missing file: {path}")
        
        file_hash = calculate_file_hash(path)
        hashes[path.name] = file_hash
        logger.debug(f"Hash for {path.name}: {file_hash}")
    
    state_data[state_key].update(hashes)
    
    # Write back to state file
    try:
        with open(state_file, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Updated artifact hashes in state file: {state_file}")
    except IOError as e:
        logger.error(f"Error writing state file {state_file}: {e}")
        raise

def run_loader(
    source_files: list,
    target_dir: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Main entry point for the loader task.
    Copies source files to data/raw, calculates their hashes, and updates the state file.
    
    Args:
        source_files: List of paths to data files (CSV) to load.
        target_dir: Optional target directory for raw data.
        
    Returns:
        Dictionary containing:
            - 'raw_files': List of paths to files in data/raw.
            - 'hashes': Dictionary of filename -> hash.
            - 'state_file': Path to the updated state file.
    """
    log_execution_start(logger, "run_loader")
    
    if not source_files:
        logger.warning("No source files provided to loader.")
        return {
            'raw_files': [],
            'hashes': {},
            'state_file': str(get_config().state_project_file)
        }
    
    raw_file_paths = []
    for source in source_files:
        raw_path = load_data_to_raw(source, target_dir)
        raw_file_paths.append(raw_path)
    
    write_artifact_hashes_to_state(raw_file_paths)
    
    config = get_config()
    result = {
        'raw_files': [str(p) for p in raw_file_paths],
        'hashes': {p.name: calculate_file_hash(p) for p in raw_file_paths},
        'state_file': str(config.state_project_file)
    }
    
    log_execution_end(logger, "run_loader")
    return result
