import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from seeds import get_seed_value

def compute_sha256(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_checksums(dir_path: Union[str, Path], pattern: Optional[str] = None) -> Dict[str, str]:
    """Compute SHA-256 hashes for all files in a directory."""
    dir_path = Path(dir_path)
    checksums = {}
    
    if pattern:
        import glob
        files = glob.glob(str(dir_path / pattern))
    else:
        files = [str(f) for f in dir_path.rglob('*') if f.is_file()]
        
    for file_path in files:
        try:
            checksums[file_path] = compute_sha256(file_path)
        except Exception as e:
            print(f"Warning: Could not hash {file_path}: {e}")
            
    return checksums

def write_checksums(checksums: Dict[str, str], output_path: Union[str, Path]):
    """Write checksums to a JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)

def read_checksums(input_path: Union[str, Path]) -> Dict[str, str]:
    """Read checksums from a JSON file."""
    input_path = Path(input_path)
    if not input_path.exists():
        return {}
        
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify_checksums(expected: Dict[str, str], actual: Dict[str, str]) -> bool:
    """Verify that actual checksums match expected ones."""
    if set(expected.keys()) != set(actual.keys()):
        return False
        
    for key, expected_val in expected.items():
        if actual.get(key) != expected_val:
            return False
    return True

def register_dataset_checksum(dataset_name: str, checksum: str, checksum_file: str = "data/checksums.json"):
    """
    Register a dataset checksum in the project's checksums file.
    Updates the entry for the given dataset_name.
    """
    path = Path(checksum_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    current_data = read_checksums(path)
    
    current_data[dataset_name] = checksum
    current_data["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    write_checksums(current_data, path)

def main():
    """Example usage of checksum utilities."""
    # This is a placeholder for CLI usage if needed
    pass

import time

if __name__ == "__main__":
    main()
