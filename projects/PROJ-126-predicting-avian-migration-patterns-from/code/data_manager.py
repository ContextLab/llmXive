import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from config import ensure_directories, calculate_sha256, DATA_RAW

def get_all_files_in_directory(directory: Path) -> List[Path]:
    """Get all files in a directory recursively."""
    return list(directory.rglob("*"))

def generate_checksums_for_raw_data() -> Dict[str, str]:
    """Generate checksums for all files in data/raw."""
    if not DATA_RAW.exists():
        return {}
    
    files = [f for f in get_all_files_in_directory(DATA_RAW) if f.is_file()]
    checksums = {}
    for file_path in files:
        relative_path = file_path.relative_to(DATA_RAW)
        checksums[str(relative_path)] = calculate_sha256(file_path)
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Optional[Path] = None):
    """Save checksums to a JSON file."""
    if output_path is None:
        output_path = DATA_RAW / "checksums.json"
    
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def verify_checksums(expected_checksums: Optional[Dict[str, str]] = None) -> bool:
    """Verify checksums of raw data files against stored values."""
    if expected_checksums is None:
        checksum_file = DATA_RAW / "checksums.json"
        if not checksum_file.exists():
            return False
        
        with open(checksum_file, 'r') as f:
            expected_checksums = json.load(f)
    
    if not expected_checksums:
        return False

    all_valid = True
    for rel_path, expected_hash in expected_checksums.items():
        file_path = DATA_RAW / rel_path
        if not file_path.exists():
            all_valid = False
            continue
        
        actual_hash = calculate_sha256(file_path)
        if actual_hash != expected_hash:
            all_valid = False
    
    return all_valid

def setup_data_directories_and_verify() -> bool:
    """Main entry point to setup directories and verify checksums."""
    ensure_directories()
    current_checksums = generate_checksums_for_raw_data()
    if current_checksums:
        save_checksums(current_checksums)
    
    return verify_checksums(current_checksums)