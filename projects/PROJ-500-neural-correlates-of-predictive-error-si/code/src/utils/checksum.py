import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, List

def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def compute_directory_checksums(directory: Path, extension_filter: Optional[str] = None) -> Dict[str, str]:
    """Compute checksums for all files in a directory."""
    checksums = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            if extension_filter is None or file_path.suffix == extension_filter:
                checksums[str(file_path)] = compute_file_sha256(file_path)
    return checksums

def save_checksum_manifest(checksums: Dict[str, str], output_path: Path):
    """Save checksums to a JSON manifest file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)

def load_checksum_manifest(manifest_path: Path) -> Dict[str, str]:
    """Load checksums from a JSON manifest file."""
    with open(manifest_path, "r") as f:
        return json.load(f)

def verify_checksums(manifest_path: Path) -> bool:
    """Verify file checksums against a manifest."""
    manifest = load_checksum_manifest(manifest_path)
    all_valid = True

    for file_path_str, expected_checksum in manifest.items():
        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"Missing file: {file_path}")
            all_valid = False
            continue

        actual_checksum = compute_file_sha256(file_path)
        if actual_checksum != expected_checksum:
            print(f"Checksum mismatch for {file_path}")
            all_valid = False

    return all_valid

def generate_and_save_manifest(directory: Path, output_path: Path, extension_filter: Optional[str] = None):
    """Generate and save a checksum manifest for a directory."""
    checksums = compute_directory_checksums(directory, extension_filter)
    save_checksum_manifest(checksums, output_path)
    return checksums
