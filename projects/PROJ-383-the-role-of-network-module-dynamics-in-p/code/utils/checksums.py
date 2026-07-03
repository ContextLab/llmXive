import hashlib
import os
import json
from pathlib import Path
from typing import Dict, Optional, List

# Constants for directory structure initialization
DATA_ROOT = Path("data")
SUBDIRECTORIES = [
    "raw_fmri",
    "raw_behavior",
    "processed",
    "results"
]
CHECKSUM_MANIFEST_FILE = DATA_ROOT / "checksum_manifest.json"
CHECKSUM_IGNORE_PATTERNS = {".DS_Store", ".gitkeep", "__pycache__"}

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a single file.
    
    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal string of the checksum.
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def compute_directory_checksum(dir_path: Path, algorithm: str = "sha256") -> Dict[str, str]:
    """
    Compute checksums for all files in a directory recursively.
    
    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use.
        
    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    checksums = {}
    if not dir_path.exists():
        return checksums
        
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(dir_path))
            # Skip ignore patterns
            if any(ignore in file_path.name for ignore in CHECKSUM_IGNORE_PATTERNS):
                continue
            checksums[rel_path] = compute_file_checksum(file_path, algorithm)
    return checksums

def save_checksums(checksums: Dict[str, Dict[str, str]], output_path: Path) -> None:
    """
    Save checksums to a JSON manifest file.
    
    Args:
        checksums: Dictionary of directory names to their file checksums.
        output_path: Path where the manifest will be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)

def load_checksums(input_path: Path) -> Dict[str, Dict[str, str]]:
    """
    Load checksums from a JSON manifest file.
    
    Args:
        input_path: Path to the manifest file.
        
    Returns:
        Dictionary of directory names to their file checksums.
    """
    if not input_path.exists():
        return {}
    with open(input_path, "r") as f:
        return json.load(f)

def verify_checksums(manifest_path: Path) -> bool:
    """
    Verify current directory checksums against a stored manifest.
    
    Args:
        manifest_path: Path to the checksum manifest.
        
    Returns:
        True if all checksums match, False otherwise.
    """
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}")
        return False
        
    stored_checksums = load_checksums(manifest_path)
    all_valid = True
    
    for dir_name, file_checksums in stored_checksums.items():
        dir_path = DATA_ROOT / dir_name
        if not dir_path.exists():
            print(f"Directory missing: {dir_path}")
            all_valid = False
            continue
            
        current_checksums = compute_directory_checksum(dir_path)
        
        for rel_path, stored_hash in file_checksums.items():
            if rel_path not in current_checksums:
                print(f"Missing file in {dir_name}: {rel_path}")
                all_valid = False
                continue
                
            if current_checksums[rel_path] != stored_hash:
                print(f"Checksum mismatch in {dir_name}/{rel_path}")
                all_valid = False
                
    if all_valid:
        print("All checksums verified successfully.")
    else:
        print("Checksum verification failed.")
        
    return all_valid

def generate_checksum_manifest() -> Dict[str, Dict[str, str]]:
    """
    Generate a fresh checksum manifest for all data subdirectories.
    
    Returns:
        Dictionary of directory names to their file checksums.
    """
    manifest = {}
    for subdir in SUBDIRECTORIES:
        dir_path = DATA_ROOT / subdir
        if dir_path.exists():
            manifest[subdir] = compute_directory_checksum(dir_path)
        else:
            manifest[subdir] = {}
    return manifest

def initialize_data_directories() -> None:
    """
    Create the required data subdirectory structure if it doesn't exist.
    """
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    for subdir in SUBDIRECTORIES:
        dir_path = DATA_ROOT / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure empty directories are tracked
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

def main():
    """
    CLI entry point for checksum operations.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python code/utils/checksums.py [init|generate|verify]")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "init":
        initialize_data_directories()
        # Generate manifest after initialization
        manifest = generate_checksum_manifest()
        save_checksums(manifest, CHECKSUM_MANIFEST_FILE)
        print(f"Manifest saved to {CHECKSUM_MANIFEST_FILE}")
        
    elif command == "generate":
        manifest = generate_checksum_manifest()
        save_checksums(manifest, CHECKSUM_MANIFEST_FILE)
        print(f"Manifest generated and saved to {CHECKSUM_MANIFEST_FILE}")
        
    elif command == "verify":
        success = verify_checksums(CHECKSUM_MANIFEST_FILE)
        sys.exit(0 if success else 1)
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
