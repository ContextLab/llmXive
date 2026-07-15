import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

def compute_file_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """Compute the checksum of a file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    hash_func = hashlib.new(algorithm)
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def compute_directory_checksums(dir_path: Union[str, Path]) -> Dict[str, str]:
    """Compute checksums for all files in a directory recursively."""
    path = Path(dir_path)
    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")
    
    checksums = {}
    for file_path in sorted(path.rglob('*')):
        if file_path.is_file():
            rel_path = file_path.relative_to(path)
            checksums[str(rel_path)] = compute_file_checksum(file_path)
    return checksums

def validate_file_checksum(file_path: Union[str, Path], expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """Validate a file against an expected checksum."""
    actual = compute_file_checksum(file_path, algorithm)
    return actual == expected_checksum

def save_checksums(checksums: Dict[str, str], output_path: Union[str, Path]) -> None:
    """Save checksums to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(checksums, f, indent=2)

def load_checksums(input_path: Union[str, Path]) -> Dict[str, str]:
    """Load checksums from a JSON file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Checksum file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def generate_checksum_manifest(dir_path: Union[str, Path], output_path: Union[str, Path]) -> Dict[str, str]:
    """Generate a manifest of checksums for a directory."""
    checksums = compute_directory_checksums(dir_path)
    save_checksums(checksums, output_path)
    return checksums

def verify_checksum_manifest(dir_path: Union[str, Path], manifest_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """Verify all files in a directory against a manifest."""
    path = Path(dir_path)
    manifest = load_checksums(manifest_path)
    errors = []
    
    for rel_path_str, expected in manifest.items():
        file_path = path / rel_path_str
        if not file_path.exists():
            errors.append(f"Missing: {rel_path_str}")
            continue
        if not validate_file_checksum(file_path, expected):
            errors.append(f"Checksum mismatch: {rel_path_str}")
    
    return len(errors) == 0, errors

def main():
    """CLI entry point for checksum utilities."""
    import argparse
    parser = argparse.ArgumentParser(description="Compute and verify file checksums")
    parser.add_argument("command", choices=["compute", "verify"], help="Command to run")
    parser.add_argument("path", help="Path to file or directory")
    parser.add_argument("--manifest", help="Path to manifest file (for verify)")
    parser.add_argument("--output", help="Output path for manifest (for compute)")
    
    args = parser.parse_args()
    
    if args.command == "compute":
        if Path(args.path).is_dir():
            if not args.output:
                raise ValueError("--output required for directory compute")
            manifest = generate_checksum_manifest(args.path, args.output)
            print(f"Computed checksums for {len(manifest)} files. Saved to {args.output}")
        else:
            checksum = compute_file_checksum(args.path)
            print(f"{args.path}: {checksum}")
    elif args.command == "verify":
        if not args.manifest:
            raise ValueError("--manifest required for verify")
        valid, errors = verify_checksum_manifest(args.path, args.manifest)
        if valid:
            print("Verification successful.")
        else:
            print("Verification failed:")
            for err in errors:
                print(f"  - {err}")
            exit(1)
