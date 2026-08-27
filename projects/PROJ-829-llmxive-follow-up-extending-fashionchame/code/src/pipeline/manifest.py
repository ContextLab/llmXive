import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

def calculate_file_hash(file_path: str) -> str:
    """Calculates SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def should_include_file(file_path: Path) -> bool:
    """Determines if a file should be included in the manifest."""
    if file_path.suffix in ['.pyc', '.pyo', '.so', '.dll', '.exe']:
        return False
    if '__pycache__' in str(file_path):
        return False
    return True

def generate_manifest(root_dir: str, exclude_dirs: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Generates a manifest of all files in the directory with their hashes.
    """
    manifest = {
        "files": {},
        "metadata": {
            "root_dir": root_dir,
            "generated_at": str(Path(root_dir).stat().st_mtime)
        }
    }

    exclude_dirs = exclude_dirs or ['.git', '__pycache__', 'venv']

    for path in Path(root_dir).rglob('*'):
        if path.is_file():
            if not should_include_file(path):
                continue
            # Check if in excluded dir
            is_excluded = False
            for exc in exclude_dirs:
                if exc in str(path):
                    is_excluded = True
                    break
            if is_excluded:
                continue

            rel_path = path.relative_to(root_dir)
            file_hash = calculate_file_hash(str(path))
            manifest["files"][str(rel_path)] = {
                "hash": file_hash,
                "size": path.stat().st_size
            }

    return manifest

def write_manifest(manifest: Dict[str, Any], output_path: str) -> None:
    """Writes the manifest to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest written to {output_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate Manifest")
    parser.add_argument('--root', type=str, default='code')
    parser.add_argument('--output', type=str, default='data/processed/manifest.json')
    args = parser.parse_args()

    manifest = generate_manifest(args.root)
    write_manifest(manifest, args.output)

if __name__ == '__main__':
    main()
