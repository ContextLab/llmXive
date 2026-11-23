import os
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any
import datetime

def create_project_structure() -> Dict[str, Any]:
    """
    Creates the required project directory structure and generates a manifest.
    
    Directories to create:
    - data/raw
    - data/processed
    - code
    - code/utils
    - code/tests
    - results
    - artifacts
    - specs/001-reward-fidelity-error-recovery/contracts
    
    Returns a manifest dictionary containing directories, timestamp, and checksum.
    """
    # Define the relative paths to create
    directories_to_create = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "code/tests",
        "results",
        "artifacts",
        "specs/001-reward-fidelity-error-recovery/contracts"
    ]

    # Ensure we are running from the project root
    # The task implies this script is run from the root of the project
    base_path = Path.cwd()
    
    created_dirs: List[str] = []
    
    for dir_path in directories_to_create:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(dir_path)
        print(f"Created directory: {full_path}")

    # Compute checksum
    # Algorithm: Recursively hash every file content (sorted by path), 
    # then hash the concatenation of those hashes.
    # Since we just created empty directories, there are no files yet in them.
    # We will hash the directory tree structure itself or just the empty state if no files exist.
    # The spec says "hashing every file content". If no files, the list of hashes is empty.
    # However, to make the checksum meaningful for the "directory tree", we should probably
    # include the directory paths themselves in the hash if no files exist, 
    # OR strictly follow "file content". 
    # Let's strictly follow: "hashing every file content (sorted by path)".
    # If no files exist in these new dirs, the list of file hashes is empty.
    # Hashing an empty string results in a specific hash.
    # But to be robust against future additions during the same run or to represent the tree:
    # We will collect all files currently in the project (excluding the ones we just created if they are empty? 
    # No, the spec says "recursively hashing every file content").
    # Let's implement exactly: find all files, sort by path, hash content, concat, hash result.
    
    all_files: List[Path] = []
    for root, _, files in os.walk(base_path):
        # Skip common non-code directories that might clutter the hash if they exist
        # but the spec implies the whole tree. Let's be strict.
        for file in files:
            file_path = Path(root) / file
            # Exclude the manifest we are about to write to avoid circular dependency issues
            if file == "structure_manifest.json":
                continue
            all_files.append(file_path)
    
    # Sort by relative path string
    all_files.sort(key=lambda p: str(p.relative_to(base_path)))
    
    file_hashes = []
    for file_path in all_files:
        try:
            with open(file_path, "rb") as f:
                content = f.read()
                file_hash = hashlib.sha256(content).hexdigest()
                file_hashes.append(file_hash)
        except Exception as e:
            print(f"Warning: Could not hash {file_path}: {e}")
    
    # Concatenate all hashes and hash the result
    combined_hash_string = "".join(file_hashes)
    final_checksum = hashlib.sha256(combined_hash_string.encode('utf-8')).hexdigest()

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    manifest = {
        "directories": created_dirs,
        "timestamp": timestamp,
        "checksum": final_checksum
    }

    # Write manifest
    manifest_path = base_path / "data" / "structure_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Manifest written to: {manifest_path}")
    return manifest

if __name__ == "__main__":
    create_project_structure()
