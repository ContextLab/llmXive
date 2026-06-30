"""
Checksum utility for data hygiene.
Implements Constitution Principle III: Ensure data integrity via checksum verification.
"""
import os
import hashlib
import json
from typing import Dict, Optional, List
from datetime import datetime

def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file using the specified algorithm.
    
    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal checksum string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verify a file's checksum against an expected value.
    
    Args:
        file_path: Path to the file.
        expected_checksum: The expected checksum string.
        algorithm: Hash algorithm to use.
        
    Returns:
        True if checksums match, False otherwise.
    """
    try:
        actual_checksum = compute_file_checksum(file_path, algorithm)
        return actual_checksum.lower() == expected_checksum.lower()
    except FileNotFoundError:
        return False

def scan_directory_for_checksums(
    data_dir: str, 
    metadata_path: str, 
    algorithm: str = "sha256"
) -> Dict:
    """
    Scan a directory for files, compute checksums, and update metadata.
    This function is the primary entry point for T009.
    
    It iterates through files in `data_dir` (specifically `data/raw/`),
    computes their checksums, and updates `data/simulation_metadata.json`
    with the results, ensuring data hygiene.
    
    Args:
        data_dir: Directory to scan (e.g., "data/raw").
        metadata_path: Path to the metadata JSON file.
        algorithm: Hash algorithm to use.
        
    Returns:
        A dictionary containing the scan results and metadata update status.
    """
    if not os.path.exists(data_dir):
        return {
            "status": "error",
            "message": f"Data directory not found: {data_dir}"
        }

    # Load existing metadata
    metadata = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    
    # Ensure 'checksums' key exists
    if "checksums" not in metadata:
        metadata["checksums"] = {}

    results = {
        "scanned_files": [],
        "updated_files": [],
        "errors": []
    }

    # Walk through the directory
    for root, _, files in os.walk(data_dir):
        for file in files:
            # Skip hidden files and the metadata file itself
            if file.startswith('.') or file.endswith('.json'):
                continue
            
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, os.path.dirname(metadata_path))
            
            try:
                checksum = compute_file_checksum(file_path, algorithm)
                
                # Check if this is a new file or if the checksum changed
                if relative_path not in metadata["checksums"]:
                    metadata["checksums"][relative_path] = {
                        "checksum": checksum,
                        "algorithm": algorithm,
                        "last_verified": datetime.now().isoformat()
                    }
                    results["updated_files"].append(relative_path)
                elif metadata["checksums"][relative_path]["checksum"] != checksum:
                    # Update if changed
                    metadata["checksums"][relative_path]["checksum"] = checksum
                    metadata["checksums"][relative_path]["last_verified"] = datetime.now().isoformat()
                    results["updated_files"].append(relative_path)
                
                results["scanned_files"].append(relative_path)
                
            except Exception as e:
                results["errors"].append({
                    "file": relative_path,
                    "error": str(e)
                })

    # Write updated metadata
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    results["metadata_path"] = metadata_path
    results["status"] = "success"
    return results

def main():
    """
    Entry point for the checksum utility script.
    Scans data/raw/ and updates data/simulation_metadata.json.
    """
    # Define paths relative to project root
    # Assuming this script runs from the project root or code/utils
    # We use relative paths as per project conventions
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_raw_dir = os.path.join(base_dir, "data", "raw")
    metadata_file = os.path.join(base_dir, "data", "simulation_metadata.json")
    
    print(f"Scanning directory: {data_raw_dir}")
    print(f"Updating metadata: {metadata_file}")
    
    if not os.path.exists(data_raw_dir):
        print(f"Warning: Directory {data_raw_dir} does not exist. Creating it.")
        os.makedirs(data_raw_dir, exist_ok=True)
    
    result = scan_directory_for_checksums(data_raw_dir, metadata_file)
    
    print(f"\nScan Status: {result['status']}")
    print(f"Files Scanned: {len(result['scanned_files'])}")
    print(f"Files Updated: {len(result['updated_files'])}")
    if result['errors']:
        print(f"Errors: {len(result['errors'])}")
        for err in result['errors']:
            print(f"  - {err['file']}: {err['error']}")
    else:
        print("No errors encountered.")

if __name__ == "__main__":
    main()
