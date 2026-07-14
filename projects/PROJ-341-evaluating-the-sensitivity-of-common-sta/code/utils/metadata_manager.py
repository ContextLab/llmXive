"""
Metadata Manager for Simulation Run Tracking.

Implements Constitution Principle VI (Reproducibility) and Principle V (Data Hygiene).
Provides a centralized mechanism to store, retrieve, and update simulation metadata
including random seeds, configuration parameters, and execution timestamps.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List

METADATA_FILE_PATH = "data/simulation_metadata.json"


def ensure_metadata_file_exists() -> None:
    """
    Ensures the metadata JSON file exists. If not, initializes it with an empty structure.
    Creates the 'data' directory if it doesn't exist.
    """
    os.makedirs(os.path.dirname(METADATA_FILE_PATH), exist_ok=True)
    
    if not os.path.exists(METADATA_FILE_PATH):
        initial_data = {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "runs": []
        }
        with open(METADATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)


def load_simulation_metadata() -> Dict[str, Any]:
    """
    Loads the current simulation metadata from disk.
    Returns an empty structure if the file doesn't exist.
    """
    ensure_metadata_file_exists()
    try:
        with open(METADATA_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # If corrupted or unreadable, return a safe default structure
        return {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "runs": []
        }


def save_simulation_metadata(data: Dict[str, Any]) -> None:
    """
    Saves the simulation metadata to disk.
    """
    ensure_metadata_file_exists()
    with open(METADATA_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


def register_run(
    run_id: str,
    config: Dict[str, Any],
    seed: int,
    checksums: Optional[Dict[str, str]] = None
) -> None:
    """
    Registers a new simulation run in the metadata file.
    
    Args:
        run_id: Unique identifier for this run (e.g., timestamp or hash).
        config: Dictionary of configuration parameters used.
        seed: The random seed used for reproducibility.
        checksums: Optional dictionary of file checksums for data hygiene.
    """
    metadata = load_simulation_metadata()
    
    new_run = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(),
        "seed": seed,
        "config": config,
        "checksums": checksums or {}
    }
    
    metadata["runs"].append(new_run)
    save_simulation_metadata(metadata)


def update_run_status(run_id: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Updates the status of an existing run.
    
    Args:
        run_id: The ID of the run to update.
        status: New status string (e.g., 'started', 'completed', 'failed').
        details: Optional dictionary of additional details (e.g., error messages, output paths).
    """
    metadata = load_simulation_metadata()
    
    for run in metadata["runs"]:
        if run["run_id"] == run_id:
            run["status"] = status
            if details:
                run["details"] = details
            else:
                run["details"] = {}
            run["updated_at"] = datetime.utcnow().isoformat()
            break
    
    save_simulation_metadata(metadata)


def get_run_history() -> List[Dict[str, Any]]:
    """
    Retrieves the full history of simulation runs.
    """
    metadata = load_simulation_metadata()
    return metadata.get("runs", [])


def compute_file_checksum(filepath: str, algorithm: str = 'sha256') -> str:
    """
    Computes the checksum of a file for data hygiene verification.
    
    Args:
        filepath: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal string of the checksum.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found for checksum: {filepath}")
    
    hash_func = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def register_dataset_checksum(
    dataset_name: str,
    filepath: str,
    checksum: Optional[str] = None
) -> None:
    """
    Registers a dataset checksum in the metadata file.
    
    Args:
        dataset_name: Name of the dataset.
        filepath: Path to the dataset file.
        checksum: Optional pre-computed checksum. If None, it is computed.
    """
    if checksum is None:
        checksum = compute_file_checksum(filepath)
    
    metadata = load_simulation_metadata()
    
    # Ensure datasets section exists
    if "datasets" not in metadata:
        metadata["datasets"] = {}
    
    metadata["datasets"][dataset_name] = {
        "filepath": filepath,
        "checksum": checksum,
        "registered_at": datetime.utcnow().isoformat()
    }
    
    save_simulation_metadata(metadata)


def main() -> None:
    """
    Command-line interface for testing metadata operations.
    """
    print("Initializing simulation metadata manager...")
    
    # Register a mock run
    mock_config = {
        "test_type": "t-test",
        "sample_size": 100,
        "effect_size": 0.5,
        "iterations": 1000
    }
    
    register_run(
        run_id="test-run-001",
        config=mock_config,
        seed=42,
        checksums={"raw_data": "dummy_checksum_123"}
    )
    
    # Verify registration
    history = get_run_history()
    print(f"Registered runs: {len(history)}")
    if history:
        print(f"Latest run ID: {history[-1]['run_id']}")
        print(f"Latest run seed: {history[-1]['seed']}")
    
    print("Metadata manager initialized successfully.")


if __name__ == "__main__":
    main()
