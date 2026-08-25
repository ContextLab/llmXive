"""
Checksum Manager for T021: Save raw downloads with checksums to state/projects.

This module handles the calculation of SHA-256 checksums for downloaded files
and updates the project state YAML file (primary source of truth) and a local
checksums.txt file (secondary).
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import yaml
from config import get_config, calculate_checksum, validate_file_integrity
from logging_config import get_logger

logger = get_logger(__name__)

def calculate_file_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Calculate SHA-256 checksum of a file, streaming in chunks to handle large files.
    
    Args:
        file_path: Path to the file to checksum
        chunk_size: Size of chunks to read (default 8KB)
        
    Returns:
        Hexadecimal SHA-256 string
        
    Raises:
        FileNotFoundError: If file does not exist
        PermissionError: If file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")
        
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
            
    return sha256_hash.hexdigest()

def load_project_state(state_file_path: Path) -> Dict[str, Any]:
    """
    Load the project state YAML file.
    
    Args:
        state_file_path: Path to the state YAML file
        
    Returns:
        Dictionary containing the project state
        
    Raises:
        FileNotFoundError: If state file does not exist
        yaml.YAMLError: If YAML parsing fails
    """
    if not state_file_path.exists():
        # Create default state structure if file doesn't exist
        default_state = {
            "project_id": "PROJ-408-investigating-the-predictive-power-of-pl",
            "artifact_hashes": {},
            "last_updated": None
        }
        logger.info(f"Creating new state file at {state_file_path}")
        return default_state
        
    with open(state_file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_project_state(state: Dict[str, Any], state_file_path: Path) -> None:
    """
    Save the project state dictionary to a YAML file.
    
    Args:
        state: The state dictionary to save
        state_file_path: Path to the state YAML file
    """
    state_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Saved project state to {state_file_path}")

def update_artifact_hash(
    artifact_name: str,
    file_path: Path,
    state_file_path: Optional[Path] = None
) -> str:
    """
    Calculate checksum for a file and update the project state.
    
    This is the primary function for T021. It:
    1. Calculates SHA-256 of the provided file
    2. Updates the primary state YAML file (state/projects/PROJ-408...yaml)
    3. Updates the secondary local checksums.txt file
    
    Args:
        artifact_name: Logical name for the artifact (e.g., "raw/18S_species_A.fasta")
        file_path: Path to the actual file on disk
        state_file_path: Optional override for state file path (uses config if None)
        
    Returns:
        The calculated SHA-256 checksum string
        
    Raises:
        FileNotFoundError: If the file or state file cannot be found/accessed
    """
    # Resolve paths
    if state_file_path is None:
        config = get_config()
        state_file_path = config.state_file_path
        
    # Calculate checksum
    logger.info(f"Calculating checksum for {file_path}")
    checksum = calculate_file_sha256(file_path)
    
    # Verify the file is readable and matches
    if not validate_file_integrity(file_path, checksum):
        raise ValueError(f"Checksum verification failed for {file_path}")
        
    # Load current state
    state = load_project_state(state_file_path)
    
    # Update artifact_hashes map (primary source of truth)
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
        
    state["artifact_hashes"][artifact_name] = {
        "checksum": checksum,
        "path": str(file_path),
        "size_bytes": file_path.stat().st_size,
        "algorithm": "sha256"
    }
    
    # Update timestamp
    from datetime import datetime
    state["last_updated"] = datetime.utcnow().isoformat()
    
    # Save updated state (primary)
    save_project_state(state, state_file_path)
    logger.info(f"Updated artifact_hashes for {artifact_name} in {state_file_path}")
    
    # Update secondary checksums.txt file
    _update_local_checksums_txt(artifact_name, checksum, file_path)
    
    return checksum

def _update_local_checksums_txt(
    artifact_name: str,
    checksum: str,
    file_path: Path
) -> None:
    """
    Update the secondary local checksums.txt file.
    
    This maintains a simple text file for quick reference, but the YAML state
    file is the primary source of truth.
    
    Args:
        artifact_name: Logical name for the artifact
        checksum: SHA-256 checksum string
        file_path: Path to the actual file
    """
    config = get_config()
    checksums_file = config.data_raw_dir / "checksums.txt"
    
    # Read existing entries
    entries = {}
    if checksums_file.exists():
        with open(checksums_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '|' in line:
                    parts = line.split('|', 1)
                    if len(parts) == 2:
                        entries[parts[0]] = parts[1]
    
    # Update or add entry
    entries[artifact_name] = checksum
    
    # Write back
    with open(checksums_file, 'w', encoding='utf-8') as f:
        f.write("# Checksums for raw data files (secondary to state YAML)\n")
        f.write("# Format: artifact_name|sha256_checksum\n")
        f.write("#\n")
        for name, cs in entries.items():
            f.write(f"{name}|{cs}\n")
    
    logger.debug(f"Updated local checksums.txt for {artifact_name}")

def verify_artifact_integrity(
    artifact_name: str,
    state_file_path: Optional[Path] = None
) -> bool:
    """
    Verify an artifact's integrity by comparing current checksum with stored value.
    
    Args:
        artifact_name: Logical name for the artifact
        state_file_path: Optional override for state file path
        
    Returns:
        True if checksum matches, False otherwise
        
    Raises:
        KeyError: If artifact_name is not found in state
    """
    if state_file_path is None:
        config = get_config()
        state_file_path = config.state_file_path
        
    state = load_project_state(state_file_path)
    
    if "artifact_hashes" not in state or artifact_name not in state["artifact_hashes"]:
        raise KeyError(f"Artifact '{artifact_name}' not found in state file")
        
    stored_info = state["artifact_hashes"][artifact_name]
    file_path = Path(stored_info["path"])
    stored_checksum = stored_info["checksum"]
    
    if not file_path.exists():
        logger.error(f"Artifact file missing: {file_path}")
        return False
        
    current_checksum = calculate_file_sha256(file_path)
    
    if current_checksum != stored_checksum:
        logger.error(f"Checksum mismatch for {artifact_name}: expected {stored_checksum}, got {current_checksum}")
        return False
        
    logger.info(f"Artifact integrity verified: {artifact_name}")
    return True

def list_artifacts(state_file_path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """
    List all registered artifacts and their metadata.
    
    Args:
        state_file_path: Optional override for state file path
        
    Returns:
        Dictionary mapping artifact names to their metadata
    """
    if state_file_path is None:
        config = get_config()
        state_file_path = config.state_file_path
        
    state = load_project_state(state_file_path)
    return state.get("artifact_hashes", {})
