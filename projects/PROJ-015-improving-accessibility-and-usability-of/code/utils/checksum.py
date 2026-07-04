import hashlib
import json
import os
from pathlib import Path
from typing import Optional

def compute_file_checksum(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def generate_checksum_file(file_path: Path, checksum_path: Optional[Path] = None):
    if checksum_path is None:
        checksum_path = file_path.with_suffix(file_path.suffix + '.sha256')
    
    checksum = compute_file_checksum(file_path)
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  {file_path.name}\n")
    return checksum_path

def verify_checksum(file_path: Path, checksum_path: Optional[Path] = None) -> bool:
    if checksum_path is None:
        checksum_path = file_path.with_suffix(file_path.suffix + '.sha256')
    
    if not checksum_path.exists():
        return False

    with open(checksum_path, 'r') as f:
        stored_checksum = f.read().split()[0]

    current_checksum = compute_file_checksum(file_path)
    return stored_checksum == current_checksum

def verify_checksums_in_directory(directory: Path) -> Dict[str, bool]:
    results = {}
    for file in directory.iterdir():
        if file.suffix.endswith('.sha256'):
            continue
        if file.is_file():
            results[str(file)] = verify_checksum(file)
    return results

def main():
    print("Checksum module loaded.")
