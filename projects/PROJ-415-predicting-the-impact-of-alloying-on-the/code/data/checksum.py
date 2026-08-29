import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from config import DATA_DIR


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def generate_checksums(directory: Path, recursive: bool = True) -> Dict[str, str]:
    """
    Generate checksums for all files in a directory.
    
    Args:
        directory: Path to the directory to scan
        recursive: If True, scan subdirectories as well
        
    Returns:
        Dictionary mapping relative file paths to their SHA256 checksums
    """
    checksums = {}
    
    if recursive:
        files = list(directory.rglob("*"))
    else:
        files = list(directory.iterdir())
    
    for file_path in files:
        if file_path.is_file():
            rel_path = file_path.relative_to(directory)
            checksums[str(rel_path)] = compute_sha256(file_path)
    
    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """Save checksums to a JSON file."""
    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)


def load_checksums(input_path: Path) -> Dict[str, str]:
    """Load checksums from a JSON file."""
    with open(input_path, "r") as f:
        return json.load(f)


def verify_checksums(checksums: Dict[str, str], directory: Path) -> List[str]:
    """
    Verify files against stored checksums.
    
    Args:
        checksums: Dictionary of expected checksums
        directory: Base directory where files are located
        
    Returns:
        List of relative paths for files that failed verification
    """
    failed = []
    
    for rel_path, expected_checksum in checksums.items():
        file_path = directory / rel_path
        
        if not file_path.exists():
            failed.append(rel_path)
            continue
        
        actual_checksum = compute_sha256(file_path)
        
        if actual_checksum != expected_checksum:
            failed.append(rel_path)
    
    return failed


def main() -> None:
    """Main entry point for checksum operations."""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage checksums for data files")
    parser.add_argument(
        "command",
        choices=["generate", "verify"],
        help="Command to execute: generate or verify"
    )
    parser.add_argument(
        "--directory",
        type=str,
        default=str(DATA_DIR),
        help="Directory to process (default: data/)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DATA_DIR / "checksums.json"),
        help="Output path for checksums file (for generate command)"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(DATA_DIR / "checksums.json"),
        help="Input path for checksums file (for verify command)"
    )
    
    args = parser.parse_args()
    
    directory = Path(args.directory)
    
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist")
        sys.exit(1)
    
    if args.command == "generate":
        print(f"Generating checksums for {directory}...")
        checksums = generate_checksums(directory)
        output_path = Path(args.output)
        save_checksums(checksums, output_path)
        print(f"Saved {len(checksums)} checksums to {output_path}")
        
    elif args.command == "verify":
        input_path = Path(args.input)
        
        if not input_path.exists():
            print(f"Error: Checksum file {input_path} does not exist")
            sys.exit(1)
        
        print(f"Verifying checksums from {input_path}...")
        checksums = load_checksums(input_path)
        failed = verify_checksums(checksums, directory)
        
        if failed:
            print(f"Verification FAILED for {len(failed)} file(s):")
            for path in failed:
                print(f"  - {path}")
            sys.exit(1)
        else:
            print(f"Verification PASSED for all {len(checksums)} file(s)")


if __name__ == "__main__":
    main()
