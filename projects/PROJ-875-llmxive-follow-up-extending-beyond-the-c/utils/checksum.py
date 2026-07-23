"""
Utility to generate SHA-256 checksums for data artifacts.
Implements Constitution Principle III.
"""
import os
import sys
import hashlib
import yaml
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any

from logger import setup_logger, configure_global_logging, get_logger

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise IOError(f"Failed to read file {file_path}: {e}")

def generate_checksums(directory: str, recursive: bool = True) -> Dict[str, str]:
    """
    Generate SHA-256 checksums for all files in a directory.
    Returns a dictionary mapping relative paths to hashes.
    """
    checksums = {}
    base_path = Path(directory)
    
    if not base_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if recursive:
        files = list(base_path.rglob("*"))
    else:
        files = list(base_path.glob("*"))

    for file_path in files:
        if file_path.is_file():
            try:
                rel_path = str(file_path.relative_to(base_path))
                checksum = calculate_sha256(str(file_path))
                checksums[rel_path] = checksum
            except Exception as e:
                logging.getLogger("checksum").warning(f"Skipping {file_path}: {e}")

    return checksums

def save_checksums(checksums: Dict[str, str], output_path: str):
    """Save checksums to a YAML file."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(checksums, f, default_flow_style=False, sort_keys=False)

def main():
    parser = argparse.ArgumentParser(description="Generate SHA-256 checksums for data artifacts.")
    parser.add_argument("--input", type=str, required=True, help="Input directory to scan.")
    parser.add_argument("--output", type=str, required=True, help="Output YAML file path.")
    parser.add_argument("--recursive", action="store_true", default=True, help="Scan recursively (default: True).")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level.")

    args = parser.parse_args()

    configure_global_logging(level=args.log_level)
    logger = get_logger("checksum")

    try:
        logger.info(f"Generating checksums for directory: {args.input}")
        checksums = generate_checksums(args.input, recursive=args.recursive)
        
        if not checksums:
            logger.warning("No files found to checksum.")
        else:
            logger.info(f"Generated {len(checksums)} checksums.")
            save_checksums(checksums, args.output)
            logger.info(f"Checksums saved to {args.output}")

    except Exception as e:
        logger.error(f"Failed to generate checksums: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
