import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from utils.config import get_project_root, get_path, ensure_dir, get_config

def verify_raw_data_integrity(
    file_path: Path, 
    expected_checksum: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Verify the SHA-256 checksum of a raw data file.
    
    Args:
        file_path: Path to the file.
        expected_checksum: Optional expected checksum.
        
    Returns:
        Tuple of (is_valid, actual_checksum).
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    actual_checksum = sha256_hash.hexdigest()
    
    if expected_checksum and actual_checksum != expected_checksum:
        return False, actual_checksum
    return True, actual_checksum

def generate_checksum_file(
    directory: Path, 
    output_path: Path
) -> None:
    """
    Generate a checksum file for all files in a directory.
    
    Args:
        directory: Directory to scan.
        output_path: Output JSON file path.
    """
    ensure_dir(output_path.parent)
    checksums = {}
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
          rel_path = file_path.relative_to(directory)
          sha256_hash = hashlib.sha256()
          with open(file_path, "rb") as f:
              for byte_block in iter(lambda: f.read(4096), b""):
                  sha256_hash.update(byte_block)
          checksums[str(rel_path)] = sha256_hash.hexdigest()
          
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)

def verify_all_raw_data(directory: Path) -> Dict[str, bool]:
    """
    Verify checksums for all files in a directory against a manifest.
    
    Args:
        directory: Directory containing raw data.
        
    Returns:
        Dictionary mapping file names to verification status.
    """
    manifest_path = directory.parent / "checksums.json"
    if not manifest_path.exists():
        return {}
        
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
        
    results = {}
    for rel_path, expected_hash in manifest.items():
        file_path = directory / rel_path
        if file_path.exists():
            is_valid, _ = verify_raw_data_integrity(file_path, expected_hash)
            results[rel_path] = is_valid
        else:
            results[rel_path] = False
            
    return results

def main() -> None:
    """Main entry point for checksum operations."""
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    
    if not raw_dir.exists():
        print("Raw data directory not found.")
        return
        
    output_path = raw_dir.parent / "checksums.json"
    generate_checksum_file(raw_dir, output_path)
    print(f"Checksums generated at {output_path}")

if __name__ == "__main__":
    main()