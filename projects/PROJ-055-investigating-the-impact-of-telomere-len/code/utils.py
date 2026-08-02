"""
Utility functions for the Telomere-Lifespan Impact project.

Provides core infrastructure for file integrity (SHA256), validation,
and state management.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


def generate_checksum(file_path: str) -> str:
    """
    Calculate the SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}") from e


def validate_file_exists(file_path: str) -> bool:
    """
    Check if a file exists at the given path.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        True if the file exists, False otherwise.
    """
    return Path(file_path).is_file()


def update_state_file(
    hash_map: Dict[str, str], 
    state_file_path: Optional[str] = None
) -> None:
    """
    Update the project state file with a new map of artifact hashes.
    
    This function serializes the provided hash_map to YAML and writes it
    to the state file, overwriting any previous content. It ensures the
    directory structure for the state file exists.
    
    Args:
        hash_map: Dictionary mapping artifact paths to their SHA256 checksums.
        state_file_path: Path to the state YAML file. Defaults to 
            'state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml'.
            
    Raises:
        IOError: If the file cannot be written.
        yaml.YAMLError: If the hash_map contains non-serializable objects.
    """
    if state_file_path is None:
        state_file_path = "state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml"
        
    state_path = Path(state_file_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            # Ensure deterministic output for reproducibility
            yaml.dump(
                hash_map, 
                f, 
                default_flow_style=False, 
                sort_keys=True,
                allow_unicode=True
            )
    except (IOError, yaml.YAMLError) as e:
        raise IOError(f"Failed to write state file {state_file_path}: {e}") from e