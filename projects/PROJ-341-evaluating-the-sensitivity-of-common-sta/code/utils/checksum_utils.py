"""
Checksum Utilities for Data Validation.

Provides functions to compute and verify file checksums to ensure data hygiene
(Constitution Principle III).
"""
import os
import json
import hashlib
from typing import Dict, Optional, List
from datetime import datetime

METADATA_PATH = "data/simulation_metadata.json"

def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Computes the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use ('sha256' or 'md5').
        
    Returns:
        Hex digest of the checksum.
    """
    if algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "md5":
        hasher = hashlib.md5()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verifies the checksum of a file against an expected value.
    
    Args:
        file_path: Path to the file.
        expected_checksum: The expected checksum value.
        algorithm: Hash algorithm used.
        
    Returns:
        True if checksum matches, False otherwise.
    """
    actual_checksum = compute_file_checksum(file_path, algorithm)
    return actual_checksum == expected_checksum

def ensure_metadata_file_exists() -> None:
    """
    Ensures the metadata file exists.
    """
    if not os.path.exists(METADATA_PATH):
        # Initialize with a minimal structure if it doesn't exist
        # This is a fallback; the main metadata manager should handle schema creation
        initial_data = {
            "metadata": {
                "project_id": "PROJ-341",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "status": "initialized"
            },
            "simulation_runs": [],
            "dataset_checksums": []
        }
        os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
        with open(METADATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)

def load_simulation_metadata() -> Dict[str, Any]:
    """
    Loads the simulation metadata.
    """
    ensure_metadata_file_exists()
    with open(METADATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_simulation_metadata(data: Dict[str, Any]) -> None:
    """
    Saves the simulation metadata.
    """
    data["metadata"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
    os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
    with open(METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def register_dataset_checksum(dataset_name: str, file_path: str, algorithm: str = "sha256") -> None:
    """
    Registers a dataset checksum in the metadata file.
    """
    data = load_simulation_metadata()
    
    checksum_value = compute_file_checksum(file_path, algorithm)
    
    entry = {
        "dataset_name": dataset_name,
        "file_path": file_path,
        "checksum_algorithm": algorithm,
        "checksum_value": checksum_value
    }
    
    # Update or append
    updated = False
    for existing in data.get("dataset_checksums", []):
        if existing["dataset_name"] == dataset_name:
            existing.update(entry)
            updated = True
            break
    
    if not updated:
        data.setdefault("dataset_checksums", []).append(entry)
    
    save_simulation_metadata(data)

def main():
    """
    CLI entry point for checksum utilities.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute and verify file checksums.")
    parser.add_argument("file_path", help="Path to the file.")
    parser.add_argument("--algorithm", default="sha256", help="Hash algorithm (sha256, md5).")
    parser.add_argument("--verify", help="Expected checksum to verify against.")
    parser.add_argument("--register", action="store_true", help="Register checksum in metadata.")
    parser.add_argument("--name", help="Name for the dataset (required if --register).")
    
    args = parser.parse_args()
    
    checksum = compute_file_checksum(args.file_path, args.algorithm)
    print(f"Checksum for {args.file_path}: {checksum}")
    
    if args.verify:
        if checksum == args.verify:
            print("Checksum VERIFIED.")
        else:
            print("Checksum MISMATCH.")
            return 1
    
    if args.register:
        if not args.name:
            print("Error: --name is required for --register")
            return 1
        register_dataset_checksum(args.name, args.file_path, args.algorithm)
        print(f"Registered checksum for {args.name} in metadata.")
        
    return 0

if __name__ == "__main__":
    exit(main())
