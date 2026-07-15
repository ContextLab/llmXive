"""
Checksum utilities for data integrity and reproducibility.

This module provides functions for:
- Computing file checksums (SHA-256)
- Verifying checksums against expected values
- Managing simulation metadata including dataset checksums
"""
import os
import json
import hashlib
from typing import Dict, Optional, List
from datetime import datetime
import uuid

METADATA_FILE = 'data/simulation_metadata.json'

def ensure_metadata_file_exists():
    """
    Ensure the simulation metadata file exists with proper schema.
    If it doesn't exist, create it with default structure.
    """
    if not os.path.exists(METADATA_FILE):
        metadata = {
            "schema_version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "schema_definition": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Simulation Metadata Schema",
                "description": "Schema for storing simulation seeds, configuration parameters, timestamps, and dataset checksums to ensure reproducibility (Constitution Principle VI) and data hygiene (Constitution Principle V).",
                "type": "object",
                "properties": {
                    "schema_version": {
                        "type": "string",
                        "description": "Version of this metadata schema"
                    },
                    "created_at": {
                        "type": "string",
                        "format": "date-time",
                        "description": "ISO 8601 timestamp when the metadata file was created"
                    },
                    "last_updated": {
                        "type": "string",
                        "format": "date-time",
                        "description": "ISO 8601 timestamp of the last modification"
                    },
                    "config": {
                        "type": "object",
                        "description": "Global simulation configuration defaults",
                        "properties": {
                            "default_alpha": {
                                "type": "number",
                                "description": "Default significance level"
                            },
                            "default_iterations": {
                                "type": "integer",
                                "description": "Default number of simulation iterations per condition"
                            },
                            "memory_limit_mb": {
                                "type": "integer",
                                "description": "RAM limit in MB (Constitution Principle VI)"
                            }
                        }
                    },
                    "runs": {
                        "type": "array",
                        "description": "List of simulation run records",
                        "items": {
                            "type": "object",
                            "required": ["run_id", "timestamp", "seed", "config", "status"],
                            "properties": {
                                "run_id": {
                                    "type": "string",
                                    "description": "Unique identifier for this run"
                                },
                                "timestamp": {
                                    "type": "string",
                                    "format": "date-time",
                                    "description": "Start time of the run"
                                },
                                "seed": {
                                    "type": "integer",
                                    "description": "Random seed used"
                                },
                                "config": {
                                    "type": "object",
                                    "description": "Configuration parameters"
                                },
                                "status": {
                                    "type": "string",
                                    "enum": ["started", "completed", "failed", "interrupted"]
                                },
                                "output_files": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "checksums": {
                                    "type": "object"
                                },
                                "error_message": {
                                    "type": "string"
                                }
                            }
                        }
                    },
                    "datasets": {
                        "type": "array",
                        "description": "List of external datasets used",
                        "items": {
                            "type": "object",
                            "required": ["name", "source", "checksum", "downloaded_at"],
                            "properties": {
                                "name": {
                                    "type": "string"
                                },
                                "source": {
                                    "type": "string"
                                },
                                "checksum": {
                                    "type": "string"
                                },
                                "downloaded_at": {
                                    "type": "string",
                                    "format": "date-time"
                                },
                                "path": {
                                    "type": "string"
                                }
                            }
                        }
                    }
                }
            },
            "runs": [],
            "datasets": [],
            "config": {
                "default_alpha": 0.05,
                "default_iterations": 10000,
                "memory_limit_mb": 7000
            }
        }
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
        
        with open(METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Created simulation metadata file: {METADATA_FILE}")
    else:
        # Ensure the directory exists even if file exists
        os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)

def load_simulation_metadata() -> Dict:
    """
    Load simulation metadata from the JSON file.
    
    Returns:
        Dictionary containing the metadata
    """
    ensure_metadata_file_exists()
    
    with open(METADATA_FILE, 'r') as f:
        return json.load(f)

def save_simulation_metadata(metadata: Dict) -> None:
    """
    Save simulation metadata to the JSON file.
    
    Args:
        metadata: Dictionary containing the metadata to save
    """
    ensure_metadata_file_exists()
    
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Compute checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hex digest of the checksum
    """
    if algorithm == 'sha256':
        hasher = hashlib.sha256()
    elif algorithm == 'md5':
        hasher = hashlib.md5()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str, 
                   algorithm: str = 'sha256') -> bool:
    """
    Verify the checksum of a file against an expected value.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm to use
        
    Returns:
        True if checksum matches, False otherwise
    """
    actual_checksum = compute_file_checksum(file_path, algorithm)
    return actual_checksum == expected_checksum

def register_run(run_config: Dict, seed: int) -> str:
    """
    Register a new simulation run in the metadata.
    
    Args:
        run_config: Configuration parameters for the run
        seed: Random seed used
        
    Returns:
        Run ID for the new run
    """
    import uuid
    
    metadata = load_simulation_metadata()
    
    run_id = str(uuid.uuid4())
    run_record = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "seed": seed,
        "config": run_config,
        "status": "started",
        "output_files": [],
        "checksums": {}
    }
    
    metadata['runs'].append(run_record)
    metadata['last_updated'] = datetime.now().isoformat()
    
    save_simulation_metadata(metadata)
    
    return run_id

def update_run_status(run_id: str, status: str, output_files: Optional[List[str]] = None,
                     checksums: Optional[Dict[str, str]] = None, 
                     error_message: Optional[str] = None) -> None:
    """
    Update the status of a registered run.
    
    Args:
        run_id: ID of the run to update
        status: New status (started, completed, failed, interrupted)
        output_files: List of output file paths
        checksums: Dictionary of file paths to checksums
        error_message: Error message if status is failed
    """
    metadata = load_simulation_metadata()
    
    for i, run in enumerate(metadata['runs']):
        if run['run_id'] == run_id:
            metadata['runs'][i]['status'] = status
            if output_files:
                metadata['runs'][i]['output_files'] = output_files
            if checksums:
                metadata['runs'][i]['checksums'] = checksums
            if error_message:
                metadata['runs'][i]['error_message'] = error_message
            metadata['last_updated'] = datetime.now().isoformat()
            save_simulation_metadata(metadata)
            return
    
    raise ValueError(f"Run ID {run_id} not found in metadata")

def get_run_history() -> List[Dict]:
    """
    Get the history of all registered runs.
    
    Returns:
        List of run records
    """
    metadata = load_simulation_metadata()
    return metadata.get('runs', [])

def register_dataset_checksum(name: str, source: str, file_path: str, 
                              checksum: str) -> None:
    """
    Register a dataset and its checksum in the metadata.
    
    Args:
        name: Dataset name
        source: Source identifier (e.g., 'ucimlrepo:197')
        file_path: Path to the dataset file
        checksum: SHA-256 checksum of the file
    """
    metadata = load_simulation_metadata()
    
    dataset_entry = {
        "name": name,
        "source": source,
        "checksum": checksum,
        "downloaded_at": datetime.now().isoformat(),
        "path": os.path.relpath(file_path, 'data')
    }
    
    # Check if dataset already exists and update, or append
    existing_datasets = metadata.get('datasets', [])
    found = False
    for i, ds in enumerate(existing_datasets):
        if ds['name'] == name:
            existing_datasets[i] = dataset_entry
            found = True
            break
    
    if not found:
        existing_datasets.append(dataset_entry)
    
    metadata['datasets'] = existing_datasets
    metadata['last_updated'] = datetime.now().isoformat()
    
    save_simulation_metadata(metadata)

def main():
    """
    Command-line interface for checksum utilities.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Checksum utilities for simulation data')
    parser.add_argument('--compute', '-c', help='Compute checksum for a file')
    parser.add_argument('--verify', '-v', nargs=2, metavar=('FILE', 'CHECKSUM'), 
                       help='Verify file checksum')
    parser.add_argument('--list', '-l', action='store_true', 
                       help='List all registered runs')
    parser.add_argument('--datasets', '-d', action='store_true',
                       help='List all registered datasets')
    
    args = parser.parse_args()
    
    if args.compute:
        checksum = compute_file_checksum(args.compute)
        print(f"{args.compute}: {checksum}")
    
    elif args.verify:
        file_path, expected = args.verify
        if verify_checksum(file_path, expected):
            print(f"✓ Checksum verified for {file_path}")
        else:
            actual = compute_file_checksum(file_path)
            print(f"✗ Checksum mismatch for {file_path}")
            print(f"  Expected: {expected}")
            print(f"  Actual:   {actual}")
    
    elif args.list:
        runs = get_run_history()
        if runs:
            print("Registered runs:")
            for run in runs:
                print(f"  {run['run_id']}: {run['status']} ({run['timestamp']})")
        else:
            print("No runs registered.")
    
    elif args.datasets:
        metadata = load_simulation_metadata()
        datasets = metadata.get('datasets', [])
        if datasets:
            print("Registered datasets:")
            for ds in datasets:
                print(f"  {ds['name']}: {ds['source']}")
                print(f"    Path: {ds['path']}")
                print(f"    Checksum: {ds['checksum'][:16]}...")
                print(f"    Downloaded: {ds['downloaded_at']}")
        else:
            print("No datasets registered.")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
