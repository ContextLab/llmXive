"""
Metadata manager for simulation and dataset tracking.
Handles checksums, run history, and simulation metadata.
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid
from code.simulation.logging_config import get_logger

logger = get_logger(__name__)

METADATA_FILE_PATH = "data/simulation_metadata.json"

def ensure_metadata_file_exists() -> None:
    """Ensure the metadata file exists, creating it if necessary."""
    os.makedirs(os.path.dirname(METADATA_FILE_PATH), exist_ok=True)
    if not os.path.exists(METADATA_FILE_PATH):
        initial_data = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "runs": [],
            "datasets": [],
            "configurations": {}
        }
        with open(METADATA_FILE_PATH, 'w') as f:
            json.dump(initial_data, f, indent=2)
        logger.info(f"Created metadata file: {METADATA_FILE_PATH}")

def load_simulation_metadata() -> Dict[str, Any]:
    """Load simulation metadata from file."""
    ensure_metadata_file_exists()
    try:
        with open(METADATA_FILE_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load metadata: {str(e)}")
        return {"version": "1.0", "runs": [], "datasets": [], "configurations": {}}

def save_simulation_metadata(data: Dict[str, Any]) -> None:
    """Save simulation metadata to file."""
    os.makedirs(os.path.dirname(METADATA_FILE_PATH), exist_ok=True)
    try:
        with open(METADATA_FILE_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved metadata to {METADATA_FILE_PATH}")
    except Exception as e:
        logger.error(f"Failed to save metadata: {str(e)}")

def compute_file_checksum(file_path: str) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal checksum string
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify file checksum against expected value.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum string
        
    Returns:
        True if checksum matches, False otherwise
    """
    try:
        actual_checksum = compute_file_checksum(file_path)
        return actual_checksum == expected_checksum
    except Exception as e:
        logger.error(f"Checksum verification failed: {str(e)}")
        return False

def register_run(run_info: Dict[str, Any]) -> str:
    """
    Register a new simulation run in metadata.
    
    Args:
        run_info: Dictionary containing run information
        
    Returns:
        Unique run ID
    """
    metadata = load_simulation_metadata()
    
    run_id = str(uuid.uuid4())
    run_record = {
        "id": run_id,
        "timestamp": datetime.now().isoformat(),
        "status": "started",
        **run_info
    }
    
    metadata["runs"].append(run_record)
    save_simulation_metadata(metadata)
    
    logger.info(f"Registered run: {run_id}")
    return run_id

def update_run_status(run_id: str, status: str, details: Optional[Dict] = None) -> None:
    """
    Update the status of a registered run.
    
    Args:
        run_id: Run ID to update
        status: New status (e.g., 'completed', 'failed')
        details: Optional additional details
    """
    metadata = load_simulation_metadata()
    
    for run in metadata["runs"]:
        if run["id"] == run_id:
            run["status"] = status
            run["completed_at"] = datetime.now().isoformat()
            if details:
                run.update(details)
            break
    
    save_simulation_metadata(metadata)
    logger.info(f"Updated run {run_id} status to {status}")

def get_run_history() -> List[Dict[str, Any]]:
    """
    Get history of all registered runs.
    
    Returns:
        List of run records
    """
    metadata = load_simulation_metadata()
    return metadata.get("runs", [])

def register_dataset_checksum(dataset_name: str, file_path: str, 
                              description: Optional[str] = None) -> None:
    """
    Register a dataset with its checksum.
    
    Args:
        dataset_name: Name of the dataset
        file_path: Path to the dataset file
        description: Optional description
    """
    metadata = load_simulation_metadata()
    
    try:
        checksum = compute_file_checksum(file_path)
    except Exception as e:
        logger.error(f"Failed to compute checksum for {dataset_name}: {str(e)}")
        return
    
    dataset_record = {
        "name": dataset_name,
        "file_path": file_path,
        "checksum": checksum,
        "registered_at": datetime.now().isoformat(),
        "description": description
    }
    
    # Check if dataset already exists and update
    existing = None
    for i, ds in enumerate(metadata["datasets"]):
        if ds["name"] == dataset_name:
            existing = i
            break
    
    if existing is not None:
        metadata["datasets"][existing] = dataset_record
    else:
        metadata["datasets"].append(dataset_record)
    
    save_simulation_metadata(metadata)
    logger.info(f"Registered dataset: {dataset_name} with checksum {checksum}")

def main():
    """Main entry point for metadata manager."""
    logger.info("Metadata manager initialized")
    ensure_metadata_file_exists()
    metadata = load_simulation_metadata()
    logger.info(f"Loaded metadata with {len(metadata.get('runs', []))} runs and {len(metadata.get('datasets', []))} datasets")

if __name__ == "__main__":
    main()
