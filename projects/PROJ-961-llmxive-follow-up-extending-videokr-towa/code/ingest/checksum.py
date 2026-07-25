"""Checksum verification for raw data integrity."""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from utils.config import get_project_root, get_path, ensure_dir, get_config

def verify_raw_data_integrity(file_path: Union[str, Path], expected_hash: str) -> bool:
    """Verify the SHA-256 hash of a file against an expected value."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() == expected_hash

def generate_checksum_file(file_path: Union[str, Path], output_path: Union[str, Path]) -> str:
    """Generate a checksum file for a given file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    hash_value = sha256_hash.hexdigest()

    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    with open(output_path, "w") as f:
        json.dump({"hash": hash_value, "file": str(file_path)}, f, indent=2)

    return hash_value

def verify_all_raw_data(data_dir: Union[str, Path], checksum_dir: Optional[Union[str, Path]] = None) -> List[Tuple[str, bool]]:
    """Verify all raw data files against their checksums."""
    data_dir = Path(data_dir)
    if checksum_dir is None:
        checksum_dir = data_dir.parent / "checksums"

    results: List[Tuple[str, bool]] = []
    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(data_dir)
            checksum_path = Path(checksum_dir) / f"{relative_path}.json"

            if checksum_path.exists():
                with open(checksum_path, "r") as f:
                    checksum_data = json.load(f)
                expected_hash = checksum_data["hash"]
                is_valid = verify_raw_data_integrity(file_path, expected_hash)
                results.append((str(file_path), is_valid))
            else:
                results.append((str(file_path), False))

    return results

def main() -> None:
    """Main entry point for checksum verification."""
    data_dir = get_path("data/raw")
    if data_dir.exists():
        results = verify_all_raw_data(data_dir)
        for file_path, is_valid in results:
            status = "OK" if is_valid else "FAILED"
            print(f"{status}: {file_path}")
    else:
        print("No raw data directory found.")
