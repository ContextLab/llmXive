"""
utils/hasher.py

Implements Constitution Principle V: Artifact Versioning.
Generates deterministic version hashes for all artifacts in a directory
to ensure reproducibility and traceability of the scientific pipeline.
"""
import os
import hashlib
import argparse
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from logger import get_logger

logger = get_logger(__name__)

def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the hash of a file using the specified algorithm.
    Reads the file in chunks to handle large files efficiently.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (default: sha256).

    Returns:
        Hexadecimal hash string.
    """
    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash file {file_path}: {e}")
        raise

def hash_directory_contents(
    input_dir: Path,
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Recursively hash all files in a directory.

    Args:
        input_dir: Root directory to hash.
        exclude_patterns: List of glob patterns to exclude (e.g., "*.log", "__pycache__").

    Returns:
        Dictionary mapping relative file paths to their hashes.
    """
    exclude_patterns = exclude_patterns or []
    hashes = {}
    input_dir = input_dir.resolve()

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    for file_path in input_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(input_dir)
            rel_str = str(rel_path)

            # Check exclusion patterns
            skip = False
            for pattern in exclude_patterns:
                if rel_str.endswith(pattern) or rel_str.startswith(pattern):
                    skip = True
                    break
                if "*" in pattern:
                    import fnmatch
                    if fnmatch.fnmatch(rel_str, pattern):
                        skip = True
                        break

            if skip:
                logger.debug(f"Skipping excluded file: {rel_str}")
                continue

            try:
                file_hash = calculate_file_hash(file_path)
                hashes[rel_str] = file_hash
                logger.debug(f"Hashed: {rel_str} -> {file_hash[:16]}...")
            except Exception as e:
                logger.warning(f"Could not hash {rel_str}: {e}")

    return hashes

def generate_artifact_manifest(
    hashes: Dict[str, str],
    input_dir: Path
) -> Dict[str, Any]:
    """
    Generate a structured manifest for the artifact versions.

    Args:
        hashes: Dictionary of relative paths to hashes.
        input_dir: The root directory that was hashed.

    Returns:
        Manifest dictionary.
    """
    manifest = {
        "version": "1.0.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source_directory": str(input_dir),
        "total_files": len(hashes),
        "artifacts": hashes
    }
    return manifest

def save_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """
    Save the manifest to a YAML file.

    Args:
        manifest: The manifest dictionary.
        output_path: Path to the output YAML file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Artifact manifest saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Generate artifact version hashes (Constitution Principle V)."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Input directory to hash (e.g., data/processed/)."
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output YAML file path (e.g., state/artifact_hashes.yaml)."
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=["*.log", "*.tmp", "__pycache__", "*.pyc"],
        help="Glob patterns to exclude from hashing."
    )

    args = parser.parse_args()

    if not args.input.is_dir():
        logger.error(f"Input path is not a directory: {args.input}")
        return 1

    try:
        logger.info(f"Scanning directory: {args.input}")
        hashes = hash_directory_contents(args.input, exclude_patterns=args.exclude)

        if not hashes:
            logger.warning("No files found to hash in the input directory.")

        manifest = generate_artifact_manifest(hashes, args.input)
        save_manifest(manifest, args.output)

        logger.info(f"Successfully hashed {len(hashes)} files.")
        return 0

    except Exception as e:
        logger.error(f"Hashing process failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())