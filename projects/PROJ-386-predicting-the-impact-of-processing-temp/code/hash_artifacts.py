import os
import sys
import hashlib
import json
from pathlib import Path
from datetime import datetime

STATE_DIR = Path("state")
MANIFEST_FILE = STATE_DIR / "download_manifest.json"

def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculates the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm (default: sha256).
        
    Returns:
        Hexadecimal string of the hash.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def hash_directory(directory: Path, pattern: str = "*") -> dict:
    """
    Calculates hashes for all files in a directory matching a pattern.
    
    Args:
        directory: Path to the directory.
        pattern: Glob pattern for files (default: "*").
        
    Returns:
        Dictionary mapping relative file paths to their hashes.
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    hashes = {}
    for file_path in directory.glob(pattern):
        if file_path.is_file():
            rel_path = file_path.relative_to(directory)
            hashes[str(rel_path)] = calculate_file_hash(file_path)
    return hashes

def save_manifest(manifest: dict, output_path: Path):
    """
    Saves the manifest dictionary to a JSON file.
    
    Args:
        manifest: Dictionary containing file metadata and hashes.
        output_path: Path to save the manifest file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest saved to {output_path}")

def main():
    """
    CLI entry point for hashing artifacts.
    Usage: python code/hash_artifacts.py --dir data/raw --output state/manifest.json
    """
    import argparse
    parser = argparse.ArgumentParser(description="Hash artifacts for integrity verification.")
    parser.add_argument('--dir', type=str, required=True, help='Directory to hash')
    parser.add_argument('--output', type=str, default=str(MANIFEST_FILE), help='Output manifest path')
    args = parser.parse_args()

    dir_path = Path(args.dir)
    output_path = Path(args.output)

    if not dir_path.exists():
        print(f"Error: Directory {dir_path} does not exist.")
        sys.exit(1)

    hashes = hash_directory(dir_path)
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "directory": str(dir_path),
        "files": [
            {"path": k, "hash": v} for k, v in hashes.items()
        ]
    }
    save_manifest(manifest, output_path)

if __name__ == "__main__":
    main()
