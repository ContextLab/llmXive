"""
Manifest generation utility for FR-024.
Generates a manifest.json file containing SHA256 content hashes for all
specified artifacts under the output and data directories.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from code.src.utils.logger import get_default_logger, AuditLogger

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA256 hash of a file's contents."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger = get_default_logger()
        logger.error(f"ERR-241: Failed to compute hash for {file_path}: {e}")
        raise

def find_artifacts(base_dir: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """
    Recursively find all files in base_dir.
    Optionally filter by extensions (e.g., ['.json', '.csv']).
    """
    artifacts = []
    if not base_dir.exists():
        return artifacts

    for root, _, files in os.walk(base_dir):
        for file in files:
            file_path = Path(root) / file
            if extensions:
                if any(file_path.suffix == ext for ext in extensions):
                    artifacts.append(file_path)
            else:
                artifacts.append(file_path)
    return artifacts

def generate_manifest(
    output_dir: Path,
    data_dir: Path,
    manifest_path: Path,
    logger: Optional[AuditLogger] = None
) -> Dict[str, Any]:
    """
    Generate a manifest.json containing SHA256 hashes for all files
    in output_dir and data_dir.

    Args:
        output_dir: Path to the output directory.
        data_dir: Path to the data directory.
        manifest_path: Path where the manifest.json will be written.
        logger: Optional logger instance.

    Returns:
        The manifest dictionary.
    """
    if logger is None:
        logger = get_default_logger()

    artifacts = {}
    directories_to_scan = [output_dir, data_dir]

    for directory in directories_to_scan:
        if not directory.exists():
            logger.warning(f"ERR-242: Directory {directory} does not exist, skipping.")
            continue

        files = find_artifacts(directory)
        for file_path in files:
            # Store relative path from project root (assuming file_path is relative to project root)
            # If file_path is absolute, make it relative to the current working directory or project root
            try:
                rel_path = file_path.relative_to(Path.cwd())
            except ValueError:
                # Fallback if relative_to fails, use absolute string or just the path string
                rel_path = file_path

            file_hash = compute_sha256(file_path)
            artifacts[str(rel_path)] = {
                "sha256": file_hash,
                "size_bytes": file_path.stat().st_size,
                "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }

    manifest = {
        "generated_at": datetime.now().isoformat(),
        "version": "1.0.0",
        "artifacts": artifacts
    }

    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest generated successfully at {manifest_path} with {len(artifacts)} entries.")
    except Exception as e:
        logger.error(f"ERR-243: Failed to write manifest to {manifest_path}: {e}")
        raise

    return manifest

def main():
    """Main entry point for script execution."""
    import sys
    from code.src.config import SEED

    # Set seed for reproducibility if any random ops were involved (none here, but good practice)
    # No random ops in this module, but we follow project convention.
    
    logger = get_default_logger()
    logger.info("Starting manifest generation...")

    # Define paths relative to project root
    project_root = Path.cwd()
    output_dir = project_root / "output"
    data_dir = project_root / "data"
    manifest_path = output_dir / "manifest.json"

    try:
        manifest = generate_manifest(output_dir, data_dir, manifest_path, logger)
        print(json.dumps(manifest, indent=2))
        sys.exit(0)
    except Exception as e:
        logger.error(f"ERR-244: Manifest generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
