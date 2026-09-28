"""
Traceability module for PROJ-525.
Handles logging of provenance metadata, including input data hashes,
and updates the project state YAML file.
"""
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from config import get_base_path, get_state_path
from utils import setup_logger, get_logger, PipelineError

# Project specific constants
PROJECT_ID = "PROJ-525-predicting-the-yield-strength-of-bcc-all"
STATE_FILE_NAME = f"{PROJECT_ID}.yaml"
INPUT_FEATURE_FILE = "data/processed/features_engineered.csv"

logger = setup_logger("traceability", level=logging.INFO)


def compute_sha256_file(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hex digest string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        PipelineError: If reading the file fails.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found for hashing: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise PipelineError(f"Failed to read file {file_path} for hashing: {e}")


def load_state(state_path: Path) -> Dict[str, Any]:
    """
    Loads the project state YAML file.
    If it doesn't exist, creates a minimal structure.
    
    Args:
        state_path: Path to the state YAML file.
        
    Returns:
        Dictionary representing the state.
    """
    if not state_path.exists():
        logger.info(f"State file {state_path} not found. Initializing new state.")
        return {
            "project_id": PROJECT_ID,
            "version": "1.0.0",
            "status": "in_progress",
            "artifacts": {},
            "provenance": {
                "input_data_hashes": {}
            }
        }
    
    try:
        with open(state_path, "r") as f:
            state = yaml.safe_load(f)
            if state is None:
                state = {
                    "project_id": PROJECT_ID,
                    "version": "1.0.0",
                    "status": "in_progress",
                    "artifacts": {},
                    "provenance": {
                        "input_data_hashes": {}
                    }
                }
            return state
    except Exception as e:
        logger.warning(f"Failed to load state file {state_path}, initializing new: {e}")
        return {
            "project_id": PROJECT_ID,
            "version": "1.0.0",
            "status": "in_progress",
            "artifacts": {},
            "provenance": {
                "input_data_hashes": {}
            }
        }


def save_state(state: Dict[str, Any], state_path: Path) -> None:
    """
    Saves the project state to a YAML file.
    
    Args:
        state: Dictionary representing the state.
        state_path: Path to the state YAML file.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(state_path, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State saved to {state_path}")
    except Exception as e:
        raise PipelineError(f"Failed to save state file {state_path}: {e}")


def log_input_provenance(input_file_rel_path: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes the SHA-256 hash of the input file and updates the state with provenance.
    
    Args:
        input_file_rel_path: Relative path to the input file from project root.
        state: Current state dictionary.
        
    Returns:
        Updated state dictionary.
        
    Raises:
        PipelineError: If the input file cannot be hashed.
    """
    base_path = get_base_path()
    input_file_path = base_path / input_file_rel_path
    
    logger.info(f"Computing SHA-256 hash for input file: {input_file_rel_path}")
    
    try:
        file_hash = compute_sha256_file(input_file_path)
    except Exception as e:
        raise PipelineError(f"Could not compute hash for {input_file_rel_path}: {e}")
    
    # Update state structure
    if "provenance" not in state:
        state["provenance"] = {"input_data_hashes": {}}
    if "input_data_hashes" not in state["provenance"]:
        state["provenance"]["input_data_hashes"] = {}
        
    state["provenance"]["input_data_hashes"][input_file_rel_path] = {
        "sha256": file_hash,
        "timestamp": "latest_run" # Placeholder for actual timestamp if needed
    }
    
    logger.info(f"Provenance logged: {input_file_rel_path} -> {file_hash}")
    return state


def update_state_file(input_file_rel_path: str = INPUT_FEATURE_FILE) -> Dict[str, Any]:
    """
    Main entry point to update the state file with input data provenance.
    
    Args:
        input_file_rel_path: Relative path to the input features file.
        
    Returns:
        The updated state dictionary.
    """
    state_path = get_state_path() / STATE_FILE_NAME
    state = load_state(state_path)
    
    state = log_input_provenance(input_file_rel_path, state)
    
    save_state(state, state_path)
    return state


def main() -> int:
    """
    CLI entry point for the traceability module.
    Logs the SHA-256 hash of the engineered features file and updates state.
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        update_state_file()
        logger.info("Traceability update completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Traceability update failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())