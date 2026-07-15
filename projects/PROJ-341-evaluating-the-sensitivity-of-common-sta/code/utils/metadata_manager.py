"""
Metadata Manager for Simulation Pipeline.

Handles creation, loading, and updating of the simulation_metadata.json file.
Ensures reproducibility by tracking seeds, configurations, and timestamps.
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

METADATA_PATH = "data/simulation_metadata.json"

def ensure_metadata_file_exists() -> None:
    """
    Ensures the metadata file exists. If not, creates it with the initial schema.
    """
    if not os.path.exists(METADATA_PATH):
        initial_data = {
            "schema_version": "1.0.0",
            "description": "Metadata schema for storing simulation seeds, configuration parameters, and execution timestamps.",
            "metadata": {
                "project_id": "PROJ-341",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "status": "initialized",
                "run_history": []
            },
            "simulation_runs": [],
            "dataset_checksums": []
        }
        os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
        with open(METADATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)

def load_simulation_metadata() -> Dict[str, Any]:
    """
    Loads the simulation metadata from disk.
    """
    if not os.path.exists(METADATA_PATH):
        ensure_metadata_file_exists()
    
    with open(METADATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_simulation_metadata(data: Dict[str, Any]) -> None:
    """
    Saves the simulation metadata to disk.
    """
    data["metadata"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
    os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
    with open(METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Computes the checksum of a file.
    """
    if algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "md5":
        hasher = hashlib.md5()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def register_run(config: Dict[str, Any], seed_config: Dict[str, Any]) -> str:
    """
    Registers a new simulation run in the metadata file.
    
    Args:
        config: Simulation configuration parameters.
        seed_config: Random seed configuration.
        
    Returns:
        The unique run_id for the new run.
    """
    ensure_metadata_file_exists()
    data = load_simulation_metadata()
    
    run_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    new_run = {
        "run_id": run_id,
        "timestamp_started": timestamp,
        "timestamp_completed": None,
        "seed_config": seed_config,
        "config": config,
        "output_files": {
            "p_values_raw": None,
            "error_rates_summary": None,
            "thresholds": None,
            "validation_metrics": None,
            "real_data_pvalues": None,
            "real_data_power": None
        },
        "dataset_checksums": [],
        "logs": None
    }
    
    data["simulation_runs"].append(new_run)
    data["metadata"]["status"] = "running"
    save_simulation_metadata(data)
    
    return run_id

def update_run_status(run_id: str, status_updates: Dict[str, Any]) -> None:
    """
    Updates the status and output paths for a specific run.
    
    Args:
        run_id: The unique ID of the run to update.
        status_updates: Dictionary of fields to update (e.g., timestamp_completed, output_files).
    """
    ensure_metadata_file_exists()
    data = load_simulation_metadata()
    
    for run in data["simulation_runs"]:
        if run["run_id"] == run_id:
            run.update(status_updates)
            if "timestamp_completed" in status_updates:
                data["metadata"]["status"] = "completed"
            save_simulation_metadata(data)
            return
    
    raise ValueError(f"Run with ID {run_id} not found.")

def get_run_history() -> List[Dict[str, Any]]:
    """
    Returns the history of all simulation runs.
    """
    ensure_metadata_file_exists()
    data = load_simulation_metadata()
    return data["simulation_runs"]

def register_dataset_checksum(dataset_name: str, file_path: str, algorithm: str = "sha256") -> None:
    """
    Registers a checksum for a dataset used in the simulation.
    """
    ensure_metadata_file_exists()
    data = load_simulation_metadata()
    
    checksum_value = compute_file_checksum(file_path, algorithm)
    
    checksum_entry = {
        "dataset_name": dataset_name,
        "file_path": file_path,
        "checksum_algorithm": algorithm,
        "checksum_value": checksum_value
    }
    
    # Check if entry already exists and update, otherwise append
    found = False
    for entry in data["dataset_checksums"]:
        if entry["dataset_name"] == dataset_name:
            entry.update(checksum_entry)
            found = True
            break
    
    if not found:
        data["dataset_checksums"].append(checksum_entry)
    
    save_simulation_metadata(data)

def main():
    """
    CLI entry point for metadata manager.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage simulation metadata.")
    parser.add_argument("--init", action="store_true", help="Initialize metadata file.")
    parser.add_argument("--register-run", action="store_true", help="Register a new run (requires --config).")
    parser.add_argument("--config", type=str, help="Path to JSON config file.")
    parser.add_argument("--update-status", action="store_true", help="Update run status (requires --run-id).")
    parser.add_argument("--run-id", type=str, help="Run ID to update.")
    
    args = parser.parse_args()
    
    if args.init:
        ensure_metadata_file_exists()
        print(f"Metadata file initialized at {METADATA_PATH}")
    elif args.register_run:
        if not args.config:
            print("Error: --config is required for --register-run")
            return
        with open(args.config, 'r') as f:
            config = json.load(f)
        # Mock seed config for CLI demo
        seed_config = {"base_seed": 42, "seed_strategy": "fixed"}
        run_id = register_run(config, seed_config)
        print(f"Registered run: {run_id}")
    elif args.update_status:
        if not args.run_id:
            print("Error: --run-id is required for --update-status")
            return
        # Mock update for CLI demo
        update_run_status(args.run_id, {"timestamp_completed": datetime.utcnow().isoformat() + "Z"})
        print(f"Updated status for run: {args.run_id}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
