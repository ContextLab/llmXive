import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any

def compute_file_checksum(filepath: str, algorithm: str = "sha256") -> str:
    """
    Computes the checksum of a file using the specified algorithm.
    """
    hash_func = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def generate_manifest(output_path: str, files: Dict[str, str], algorithm: str = "sha256") -> None:
    """
    Generates a manifest.json file containing checksums for the specified files.
    
    Args:
        output_path: Path to the output manifest.json file.
        files: Dictionary mapping logical names to file paths.
        algorithm: Hash algorithm to use (default: sha256).
    """
    manifest = {
        "algorithm": algorithm,
        "files": {}
    }
    
    for name, path in files.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found for checksum: {path}")
        checksum = compute_file_checksum(path, algorithm)
        manifest["files"][name] = {
            "path": str(path),
            "checksum": checksum
        }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def main():
    """
    Entry point to generate the state manifest.
    """
    # Define the files to checksum based on task T049a requirements
    files_to_check = {
        "descriptors_parquet": "data/processed/descriptors.parquet",
        "cluster_map_csv": "data/processed/cluster_map.csv"
    }
    
    output_path = "state/manifest.json"
    
    try:
        generate_manifest(output_path, files_to_check)
        print(f"Manifest generated successfully at {output_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error generating manifest: {e}")
        raise

if __name__ == "__main__":
    main()
