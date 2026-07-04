"""
Manifest generation utility for FR-024.
Computes SHA256 hashes for all generated files in the output and data directories
and writes them to output/manifest.json.
"""
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.config import SEED

logger = get_default_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def find_files_to_hash(base_dir: Path, exclude_patterns: Optional[List[str]] = None) -> List[Path]:
    """
    Find all files in the given directory recursively.
    Excludes files matching exclude_patterns.
    """
    exclude_patterns = exclude_patterns or []
    files = []
    for file_path in base_dir.rglob("*"):
        if file_path.is_file():
            # Check if file matches any exclude pattern
            should_exclude = False
            for pattern in exclude_patterns:
                if pattern in str(file_path):
                    should_exclude = True
                    break
            if not should_exclude:
                files.append(file_path)
    return sorted(files)

def generate_manifest(
    output_dir: Path,
    data_dir: Path,
    manifest_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate a manifest containing SHA256 hashes for all files in output and data directories.

    Args:
        output_dir: Path to the output directory
        data_dir: Path to the data directory
        manifest_path: Optional path to write the manifest to

    Returns:
        Dictionary containing the manifest data
    """
    logger.info(f"Generating manifest for output_dir={output_dir}, data_dir={data_dir}")

    exclude_patterns = ["__pycache__", "*.pyc", ".git", "manifest.json"]
    
    all_files = []
    all_files.extend(find_files_to_hash(output_dir, exclude_patterns))
    all_files.extend(find_files_to_hash(data_dir, exclude_patterns))

    manifest_data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "files": {}
    }

    for file_path in all_files:
        try:
            relative_path = file_path.relative_to(output_dir.parent)
            file_hash = compute_sha256(file_path)
            manifest_data["files"][str(relative_path)] = {
                "sha256": file_hash,
                "size_bytes": file_path.stat().st_size
            }
            logger.debug(f"Hashed {relative_path}: {file_hash[:16]}...")
        except Exception as e:
            logger.warning(f"Failed to hash {file_path}: {e}")
            # Continue with other files

    if manifest_path:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        logger.info(f"Manifest written to {manifest_path}")

    return manifest_data

def validate_manifest(manifest_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate that all files in the manifest exist and have matching hashes.

    Args:
        manifest_path: Path to the manifest file

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    if not manifest_path.exists():
        errors.append(f"Manifest file not found: {manifest_path}")
        return False, errors

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    project_root = manifest_path.parent.parent.parent
    
    for relative_path, file_info in manifest_data.get("files", {}).items():
        full_path = project_root / relative_path
        
        if not full_path.exists():
            errors.append(f"File missing: {relative_path}")
            continue

        expected_hash = file_info.get("sha256")
        actual_hash = compute_sha256(full_path)
        
        if expected_hash != actual_hash:
            errors.append(f"Hash mismatch for {relative_path}: expected {expected_hash}, got {actual_hash}")

    return len(errors) == 0, errors

def main():
    """Main entry point for manifest generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate manifest with SHA256 hashes")
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    parser.add_argument("--manifest-path", type=str, default="output/manifest.json", help="Manifest output path")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    data_dir = Path(args.data_dir).resolve()
    manifest_path = Path(args.manifest_path).resolve()

    if not output_dir.exists():
        logger.error(f"Output directory does not exist: {output_dir}")
        return 1
    
    if not data_dir.exists():
        logger.error(f"Data directory does not exist: {data_dir}")
        return 1

    manifest_data = generate_manifest(output_dir, data_dir, manifest_path)
    
    # Validate the generated manifest
    is_valid, errors = validate_manifest(manifest_path)
    if not is_valid:
        logger.error("Manifest validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return 1

    logger.info("Manifest generation and validation completed successfully")
    return 0

if __name__ == "__main__":
    exit(main())
