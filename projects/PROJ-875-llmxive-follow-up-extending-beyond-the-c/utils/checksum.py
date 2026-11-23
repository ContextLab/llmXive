"""
utils/checksum.py

Implements Constitution Principle III: Data Integrity via SHA-256 Checksums.
Generates SHA-256 checksums for all files in the data/processed/ directory.
Outputs a YAML manifest file mapping relative file paths to their checksums.
"""
import os
import sys
import hashlib
import argparse
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path to allow imports if needed (though this script is standalone)
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_INPUT_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_OUTPUT_FILE = PROJECT_ROOT / "state" / "checksums.yaml"


def calculate_sha256(file_path: Path) -> str:
    """
    Calculates the SHA-256 hash of a file.
    Reads the file in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Failed to calculate checksum for {file_path}: {e}")


def generate_checksums(input_dir: Path) -> Dict[str, str]:
    """
    Recursively scans input_dir and generates a dictionary of relative paths to checksums.
    Skips directories and hidden files (starting with .).
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    checksums: Dict[str, str] = {}
    file_count = 0

    for root, _, files in os.walk(input_dir):
        for filename in files:
            if filename.startswith('.'):
                continue
            
            file_path = Path(root) / filename
            rel_path = file_path.relative_to(input_dir)
            
            checksum = calculate_sha256(file_path)
            checksums[str(rel_path)] = checksum
            file_count += 1

    if file_count == 0:
        print(f"Warning: No files found in {input_dir}")
    
    return checksums


def save_manifest(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Saves the checksums to a YAML file.
    Includes metadata: timestamp, input directory, and file count.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "input_directory": str(output_path.parent.parent / "data" / "processed"),
        "algorithm": "SHA-256",
        "file_count": len(checksums),
        "checksums": checksums
    }

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    
    print(f"Checksum manifest saved to: {output_path}")
    print(f"Total files checksummed: {len(checksums)}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate SHA-256 checksums for data/processed/ directory."
    )
    parser.add_argument(
        "--input", 
        type=Path, 
        default=DEFAULT_INPUT_DIR,
        help=f"Directory to scan for files (default: {DEFAULT_INPUT_DIR})"
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        default=DEFAULT_OUTPUT_FILE,
        help=f"Output YAML file path (default: {DEFAULT_OUTPUT_FILE})"
    )
    
    args = parser.parse_args()
    
    try:
        checksums = generate_checksums(args.input)
        save_manifest(checksums, args.output)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except NotADirectoryError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()