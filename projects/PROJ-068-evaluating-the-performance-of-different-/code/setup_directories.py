"""
Setup script to create the project directory structure.

This script creates the directories required for T001:
projects/PROJ-068-evaluating-the-performance-of-different-/code/
projects/PROJ-068-evaluating-the-performance-of-different-/tests/
projects/PROJ-068-evaluating-the-performance-of-different-/data/
projects/PROJ-068-evaluating-the-performance-of-different-/results/
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return ""

def setup_directories(base_path: Path) -> List[Path]:
    """
    Create the required directory structure.
    
    Args:
        base_path: The root path where the project directories will be created.
        
    Returns:
        List of created directory paths.
    """
    project_name = "PROJ-068-evaluating-the-performance-of-different-"
    project_root = base_path / project_name
    
    required_dirs = [
        project_root / "code",
        project_root / "tests",
        project_root / "data",
        project_root / "results",
    ]
    
    created_dirs = []
    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(dir_path)
        print(f"Created directory: {dir_path}")
        
    return created_dirs

def generate_checksums(directory: Path, checksum_file: Path) -> Dict[str, str]:
    """
    Generate checksums for all files in a directory recursively.
    
    Args:
        directory: The directory to scan.
        checksum_file: Path to the JSON file to write checksums to.
        
    Returns:
        Dictionary of relative paths to checksums.
    """
    checksums = {}
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(directory)
            checksum = compute_file_checksum(file_path)
            checksums[str(rel_path)] = checksum
            
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)
        
    return checksums

def verify_directories(base_path: Path) -> bool:
    """
    Verify that the required directories exist.
    
    Args:
        base_path: The root path to check.
        
    Returns:
        True if all directories exist, False otherwise.
    """
    project_name = "PROJ-068-evaluating-the-performance-of-different-"
    project_root = base_path / project_name
    
    required_dirs = [
        project_root / "code",
        project_root / "tests",
        project_root / "data",
        project_root / "results",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if not dir_path.exists() or not dir_path.is_dir():
            print(f"Missing directory: {dir_path}")
            all_exist = False
            
    return all_exist

def main():
    """Main entry point for the setup script."""
    base_path = Path("projects")
    
    print(f"Setting up project structure in: {base_path}")
    
    # Create directories
    created = setup_directories(base_path)
    
    if not created:
        print("ERROR: Failed to create any directories.")
        return 1
        
    print(f"\nSuccessfully created {len(created)} directories.")
    
    # Verify
    if verify_directories(base_path):
        print("Verification PASSED: All required directories exist.")
        return 0
    else:
        print("Verification FAILED: Some directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
