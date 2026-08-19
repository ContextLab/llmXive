import os
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def generate_checksum_manifest(base_dir: Path, relative_paths: List[str], output_path: Path) -> Dict:
    """
    Generate a JSON manifest of checksums for a list of files relative to base_dir.
    
    Args:
        base_dir: The root directory containing the files.
        relative_paths: List of relative file paths to include.
        output_path: Path where the manifest JSON will be written.
    
    Returns:
        The manifest dictionary.
    """
    manifest = {
        "base_dir": str(base_dir),
        "files": {}
    }

    for rel_path in relative_paths:
        full_path = base_dir / rel_path
        if not full_path.exists():
            logger.warning(f"File missing for manifest generation: {full_path}")
            continue
        
        checksum = compute_file_checksum(full_path)
        manifest["files"][rel_path] = checksum

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Checksum manifest written to {output_path}")
    return manifest

def verify_checksums(base_dir: Path, manifest_path: Path) -> Tuple[bool, List[str]]:
    """
    Verify files against a checksum manifest.
    
    Args:
        base_dir: The root directory containing the files.
        manifest_path: Path to the JSON manifest.
    
    Returns:
        Tuple of (all_valid, list_of_failed_files).
    """
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        return False, ["Manifest not found"]

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest: {e}")
        return False, ["Invalid manifest JSON"]

    failed_files = []
    all_valid = True

    for rel_path, expected_checksum in manifest.get("files", {}).items():
        full_path = base_dir / rel_path
        if not full_path.exists():
            logger.error(f"File missing during verification: {full_path}")
            failed_files.append(rel_path)
            all_valid = False
            continue

        try:
            actual_checksum = compute_file_checksum(full_path)
            if actual_checksum != expected_checksum:
                logger.error(f"Checksum mismatch for {full_path}: expected {expected_checksum}, got {actual_checksum}")
                failed_files.append(rel_path)
                all_valid = False
            else:
                logger.debug(f"Checksum verified for {full_path}")
        except Exception as e:
            logger.error(f"Error verifying {full_path}: {e}")
            failed_files.append(rel_path)
            all_valid = False

    return all_valid, failed_files

def initialize_data_structure(data_root: Path) -> None:
    """
    Initialize the required directory structure for the data pipeline.
    Creates: raw/, processed/, validation/
    """
    sub_dirs = ["raw", "processed", "validation"]
    for subdir in sub_dirs:
        dir_path = data_root / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create a .gitkeep to ensure directories are tracked in git
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
        logger.info(f"Initialized directory: {dir_path}")

def main():
    """
    CLI entry point for checksum utilities.
    Usage:
      - Initialize: python code/utils/checksum_utils.py init
      - Generate: python code/utils/checksum_utils.py generate <relative_path1> [relative_path2] ...
      - Verify: python code/utils/checksum_utils.py verify
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python code/utils/checksum_utils.py <command> [args]")
        print("Commands: init, generate, verify")
        sys.exit(1)

    command = sys.argv[1]
    # Assume data root is relative to script location or current dir
    # For this project, we assume running from project root
    data_root = Path("./data").resolve()

    if command == "init":
        initialize_data_structure(data_root)
        print(f"Data structure initialized at {data_root}")
    
    elif command == "generate":
        if len(sys.argv) < 3:
            print("Usage: generate <relative_path1> [relative_path2] ...")
            sys.exit(1)
        relative_paths = sys.argv[2:]
        manifest_path = data_root / "manifest.json"
        generate_checksum_manifest(data_root, relative_paths, manifest_path)
        print(f"Manifest generated at {manifest_path}")
    
    elif command == "verify":
        manifest_path = data_root / "manifest.json"
        all_valid, failed = verify_checksums(data_root, manifest_path)
        if all_valid:
            print("All checksums verified successfully.")
        else:
            print(f"Verification failed for {len(failed)} files: {failed}")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
