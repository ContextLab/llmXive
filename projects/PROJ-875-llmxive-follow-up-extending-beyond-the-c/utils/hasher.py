"""
utils/hasher.py

Generates version hashes for artifacts to ensure reproducibility and traceability
(Constitution Principle V).

This utility computes SHA-256 hashes for all files in a specified input directory
(recursively) and writes the results to a YAML output file.

Usage:
    python utils/hasher.py --input <input_dir> --output <output_file>
"""

import os
import sys
import hashlib
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Ensure we can import from the project root if needed, though this script is self-contained
# If running from project root: python utils/hasher.py ...
# If running from inside utils: python hasher.py ...
# We rely on standard library only.

def compute_file_hash(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Failed to hash file {file_path}: {e}")

def hash_directory(input_dir: Path) -> Dict[str, Any]:
    """
    Recursively hashes all files in a directory.

    Args:
        input_dir: Path to the directory to hash.

    Returns:
        Dictionary containing hash metadata.
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    files_data = []
    total_files = 0

    for root, _, files in os.walk(input_dir):
        for filename in files:
            file_path = Path(root) / filename
            # Skip hidden files or common temporary files if necessary,
            # but for now, hash everything to ensure integrity.
            if filename.startswith('.'):
                continue

            try:
                file_hash = compute_file_hash(file_path)
                relative_path = file_path.relative_to(input_dir)
                
                # Get file stats
                stat = file_path.stat()
                
                files_data.append({
                    "path": str(relative_path),
                    "sha256": file_hash,
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
                total_files += 1
            except Exception as e:
                # Log error but continue processing other files
                print(f"Warning: Skipping {file_path} due to error: {e}", file=sys.stderr)

    return {
        "generated_at": datetime.now().isoformat(),
        "input_directory": str(input_dir),
        "total_files": total_files,
        "files": files_data
    }

def save_hash_report(data: Dict[str, Any], output_path: Path) -> None:
    """
    Saves the hash report to a YAML file.

    Args:
        data: The hash data dictionary.
        output_path: Path to the output file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    print(f"Hash report saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Generate version hashes for artifacts (Constitution Principle V)."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input directory to hash (e.g., data/processed/)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output YAML file path (e.g., state/artifact_hashes.yaml)"
    )

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_path = Path(args.output)

    try:
        print(f"Scanning directory: {input_dir}")
        hash_data = hash_directory(input_dir)
        print(f"Found {hash_data['total_files']} files.")
        save_hash_report(hash_data, output_path)
        print("Hash generation completed successfully.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()