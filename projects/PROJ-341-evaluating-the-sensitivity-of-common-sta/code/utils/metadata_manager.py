"""Metadata manager for simulation runs and dataset checksums."""
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

from code.simulation.logging_config import get_logger

# Global logger instance
_logger = get_logger(__name__)

METADATA_FILE_PATH = "data/simulation_metadata.json"


def ensure_metadata_file_exists() -> str:
    """Ensure the metadata file exists, creating an empty structure if not.

    Returns:
        The path to the metadata file.
    """
    os.makedirs(os.path.dirname(METADATA_FILE_PATH), exist_ok=True)
    if not os.path.exists(METADATA_FILE_PATH):
        initial_data = {
            "runs": [],
            "datasets": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        with open(METADATA_FILE_PATH, 'w') as f:
            json.dump(initial_data, f, indent=2)
        _logger.log("metadata_file_created", path=METADATA_FILE_PATH)
    return METADATA_FILE_PATH


def load_simulation_metadata() -> Dict[str, Any]:
    """Load the simulation metadata from disk.

    Returns:
        The metadata dictionary.
    """
    ensure_metadata_file_exists()
    with open(METADATA_FILE_PATH, 'r') as f:
        return json.load(f)


def save_simulation_metadata(data: Dict[str, Any]) -> None:
    """Save the simulation metadata to disk.

    Args:
        data: The metadata dictionary to save.
    """
    data["updated_at"] = datetime.utcnow().isoformat()
    with open(METADATA_FILE_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    _logger.log("metadata_file_saved", path=METADATA_FILE_PATH)


def compute_file_checksum(file_path: str) -> str:
    """Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        The SHA-256 checksum as a hexadecimal string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify the checksum of a file against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: The expected SHA-256 checksum.

    Returns:
        True if the checksum matches, False otherwise.
    """
    actual_checksum = compute_file_checksum(file_path)
    return actual_checksum == expected_checksum


def register_run(run_params: Dict[str, Any]) -> str:
    """Register a new simulation run in the metadata.

    Args:
        run_params: Parameters of the run (e.g., sample sizes, iterations).

    Returns:
        The unique run ID.
    """
    ensure_metadata_file_exists()
    data = load_simulation_metadata()

    run_id = str(uuid.uuid4())
    run_entry = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(),
        "parameters": run_params,
        "status": "completed"
    }

    data["runs"].append(run_entry)
    save_simulation_metadata(data)
    _logger.log("run_registered", run_id=run_id)
    return run_id


def update_run_status(run_id: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Update the status of a registered run.

    Args:
        run_id: The unique run ID.
        status: The new status (e.g., "completed", "failed").
        details: Optional additional details about the run.
    """
    ensure_metadata_file_exists()
    data = load_simulation_metadata()

    for run in data["runs"]:
        if run["run_id"] == run_id:
            run["status"] = status
            if details:
                run["details"] = details
            break

    save_simulation_metadata(data)
    _logger.log("run_status_updated", run_id=run_id, status=status)


def get_run_history(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve the history of registered runs.

    Args:
        limit: Optional limit on the number of runs to return.

    Returns:
        List of run entries.
    """
    ensure_metadata_file_exists()
    data = load_simulation_metadata()
    runs = data.get("runs", [])
    if limit:
        runs = runs[-limit:]
    return runs


def register_dataset_checksum(dataset_name: str, file_path: str, dataset_id: Optional[str] = None) -> None:
    """Register a dataset and its checksum in the metadata.

    Args:
        dataset_name: Name of the dataset.
        file_path: Path to the dataset file.
        dataset_id: Optional source dataset ID (e.g., UCI ID).
    """
    ensure_metadata_file_exists()
    data = load_simulation_metadata()

    checksum = compute_file_checksum(file_path)

    dataset_entry = {
        "name": dataset_name,
        "file_path": file_path,
        "checksum": checksum,
        "dataset_id": dataset_id,
        "registered_at": datetime.utcnow().isoformat()
    }

    # Avoid duplicates
    existing = [d for d in data["datasets"] if d["file_path"] == file_path]
    if not existing:
        data["datasets"].append(dataset_entry)
        save_simulation_metadata(data)
        _logger.log("dataset_registered", name=dataset_name, checksum=checksum)


def main() -> None:
    """Main entry point for metadata management CLI (for testing)."""
    print("Metadata Manager CLI")
    print(f"Metadata file: {METADATA_FILE_PATH}")
    data = load_simulation_metadata()
    print(f"Runs: {len(data.get('runs', []))}")
    print(f"Datasets: {len(data.get('datasets', []))}")
