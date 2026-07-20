"""
State Manager Module for llmXive Pipeline

This module provides functionality to track derived files using a state.yaml file.
It manages checksums, timestamps, and file metadata to ensure reproducibility
and detect changes in the pipeline's outputs.
"""
import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from config import get_project_root

logger = logging.getLogger(__name__)

STATE_FILE_PATH = "state.yaml"

def _compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum

    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state() -> Dict[str, Any]:
    """
    Load the state.yaml file from the project root.

    Returns:
        Dictionary containing the state data, or empty dict if file doesn't exist.
    """
    project_root = get_project_root()
    state_path = project_root / STATE_FILE_PATH

    if not state_path.exists():
        logger.info(f"State file not found at {state_path}. Starting with empty state.")
        return {
            "metadata": {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": None
            },
            "files": {}
        }

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f)
            if state is None:
                return {
                    "metadata": {
                        "version": "1.0",
                        "created_at": datetime.now().isoformat(),
                        "last_updated": None
                    },
                    "files": {}
                }
            return state
    except yaml.YAMLError as e:
        logger.error(f"Error parsing state file: {e}")
        raise

def save_state(state: Dict[str, Any]) -> None:
    """
    Save the state dictionary to state.yaml.

    Args:
        state: The state dictionary to save
    """
    project_root = get_project_root()
    state_path = project_root / STATE_FILE_PATH

    state["metadata"]["last_updated"] = datetime.now().isoformat()

    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    logger.info(f"State saved to {state_path}")

def register_file(file_path: str, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Register a file in the state, computing its checksum and metadata.

    Args:
        file_path: Relative path to the file from project root
        state: Optional existing state dict. If None, loads from disk.

    Returns:
        Updated state dictionary
    """
    if state is None:
        state = load_state()

    project_root = get_project_root()
    full_path = project_root / file_path

    if not full_path.exists():
        raise FileNotFoundError(f"Cannot register file: {full_path} does not exist.")

    checksum = _compute_file_checksum(full_path)
    file_stat = full_path.stat()

    file_entry = {
        "path": file_path,
        "checksum": checksum,
        "size_bytes": file_stat.st_size,
        "last_modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
        "registered_at": datetime.now().isoformat()
    }

    state["files"][file_path] = file_entry
    logger.info(f"Registered file: {file_path} (checksum: {checksum[:16]}...)")

    return state

def verify_file(file_path: str, state: Optional[Dict[str, Any]] = None) -> bool:
    """
    Verify that a registered file's checksum matches its current state.

    Args:
        file_path: Relative path to the file from project root
        state: Optional existing state dict. If None, loads from disk.

    Returns:
        True if checksum matches, False otherwise.
    """
    if state is None:
        state = load_state()

    if file_path not in state.get("files", {}):
        logger.warning(f"File {file_path} is not registered in state.")
        return False

    registered_entry = state["files"][file_path]
    project_root = get_project_root()
    full_path = project_root / file_path

    if not full_path.exists():
        logger.error(f"File {file_path} exists in state but not on disk.")
        return False

    current_checksum = _compute_file_checksum(full_path)

    if current_checksum != registered_entry["checksum"]:
        logger.error(f"Checksum mismatch for {file_path}. "
                     f"Expected: {registered_entry['checksum']}, "
                     f"Got: {current_checksum}")
        return False

    logger.info(f"Verification passed for {file_path}")
    return True

def verify_all(state: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
    """
    Verify all registered files in the state.

    Args:
        state: Optional existing state dict. If None, loads from disk.

    Returns:
        Dictionary mapping file paths to verification results (True/False)
    """
    if state is None:
        state = load_state()

    results = {}
    for file_path in state.get("files", {}).keys():
        results[file_path] = verify_file(file_path, state)

    all_valid = all(results.values())
    if all_valid:
        logger.info("All registered files verified successfully.")
    else:
        failed = [p for p, v in results.items() if not v]
        logger.warning(f"Verification failed for {len(failed)} files: {failed}")

    return results

def get_file_info(file_path: str, state: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Get metadata for a registered file.

    Args:
        file_path: Relative path to the file from project root
        state: Optional existing state dict. If None, loads from disk.

    Returns:
        Dictionary with file metadata, or None if not registered.
    """
    if state is None:
        state = load_state()

    return state.get("files", {}).get(file_path)

def clear_stale_entries(state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Remove entries from state for files that no longer exist on disk.

    Args:
        state: Optional existing state dict. If None, loads from disk.

    Returns:
        Updated state dictionary with stale entries removed.
    """
    if state is None:
        state = load_state()

    project_root = get_project_root()
    stale_files = []

    for file_path in list(state.get("files", {}).keys()):
        full_path = project_root / file_path
        if not full_path.exists():
            stale_files.append(file_path)
            del state["files"][file_path]

    if stale_files:
        logger.info(f"Removed {len(stale_files)} stale entries: {stale_files}")

    return state

def initialize_state() -> Dict[str, Any]:
    """
    Initialize a new state.yaml file with default structure.

    Returns:
        The newly created state dictionary.
    """
    state = {
        "metadata": {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": None,
            "description": "Tracks checksums and metadata for pipeline derived files"
        },
        "files": {}
    }
    save_state(state)
    logger.info("Initialized new state.yaml file.")
    return state
