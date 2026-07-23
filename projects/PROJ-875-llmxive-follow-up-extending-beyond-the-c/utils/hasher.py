"""
Utility to generate version hashes for artifacts.
Implements Constitution Principle V.
"""
import os
import sys
import hashlib
import yaml
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from logger import setup_logger, configure_global_logging, get_logger

def calculate_content_hash(directory: str, recursive: bool = True) -> str:
    """
    Calculate a composite hash for a directory based on file contents and paths.
    This serves as a version identifier for the dataset/artifacts.
    """
    sha256_hash = hashlib.sha256()
    base_path = Path(directory)

    if not base_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    # Sort files to ensure deterministic order
    if recursive:
        files = sorted(base_path.rglob("*"))
    else:
        files = sorted(base_path.glob("*"))

    for file_path in files:
        if file_path.is_file():
            try:
                rel_path = str(file_path.relative_to(base_path))
                # Include path in hash
                sha256_hash.update(rel_path.encode('utf-8'))
                # Include content in hash
                with open(file_path, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
            except Exception as e:
                logging.getLogger("hasher").warning(f"Skipping {file_path}: {e}")

    return sha256_hash.hexdigest()

def generate_version_hash(directory: str, output_path: str, recursive: bool = True):
    """
    Generate a version hash for a directory and save it to a YAML file.
    """
    try:
        version_hash = calculate_content_hash(directory, recursive=recursive)
        
        version_info = {
            "directory": directory,
            "version_hash": version_hash,
            "generated_at": datetime.utcnow().isoformat(),
            "recursive": recursive
        }

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(version_info, f, default_flow_style=False, sort_keys=False)

        return version_info

    except Exception as e:
        raise IOError(f"Failed to generate version hash: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate version hashes for artifacts.")
    parser.add_argument("--input", type=str, required=True, help="Input directory to hash.")
    parser.add_argument("--output", type=str, required=True, help="Output YAML file path.")
    parser.add_argument("--recursive", action="store_true", default=True, help="Hash recursively (default: True).")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level.")

    args = parser.parse_args()

    configure_global_logging(level=args.log_level)
    logger = get_logger("hasher")

    try:
        logger.info(f"Generating version hash for directory: {args.input}")
        version_info = generate_version_hash(args.input, args.output, recursive=args.recursive)
        logger.info(f"Version hash generated: {version_info['version_hash']}")
        logger.info(f"Version info saved to {args.output}")

    except Exception as e:
        logger.error(f"Failed to generate version hash: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
