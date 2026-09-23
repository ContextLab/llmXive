import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """
    Returns the project root directory.
    Assumes the script is run from the project root or code/ directory.
    """
    current = Path.cwd()
    # Check if we are in code/
    if current.name == "code":
        return current.parent
    # Check if we are in the root
    if (current / "data" / "raw").exists() and (current / "specs").exists():
        return current
    # Fallback: traverse up
    for parent in current.parents:
        if (parent / "data" / "raw").exists() and (parent / "specs").exists():
            return parent
    raise FileNotFoundError("Could not determine project root")

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Computes the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the checksum.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def load_checksum_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Loads the checksum manifest file.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        Dictionary containing the manifest data.
    """
    if not manifest_path.exists():
        logger.warning(f"Manifest not found at {manifest_path}. Initializing empty manifest.")
        return {"files": {}}

    try:
        with open(manifest_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest {manifest_path}: {e}")
        raise
    except IOError as e:
        logger.error(f"Error reading manifest {manifest_path}: {e}")
        raise

def save_checksum_manifest(manifest: Dict[str, Any], manifest_path: Path) -> None:
    """
    Saves the checksum manifest to a JSON file.

    Args:
        manifest: Dictionary containing the manifest data.
        manifest_path: Path to save the manifest.
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest saved to {manifest_path}")
    except IOError as e:
        logger.error(f"Error saving manifest {manifest_path}: {e}")
        raise

def verify_checksum(file_path: Path, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verifies the checksum of a single file against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected checksum string.
        algorithm: Hash algorithm to use.

    Returns:
        True if checksum matches, False otherwise.
    """
    try:
        actual_checksum = compute_file_checksum(file_path, algorithm)
        if actual_checksum == expected_checksum:
            logger.info(f"Checksum verified for {file_path.name}")
            return True
        else:
            logger.error(f"Checksum MISMATCH for {file_path.name}. "
                         f"Expected: {expected_checksum}, Got: {actual_checksum}")
            return False
    except FileNotFoundError as e:
        logger.error(f"File not found during verification: {e}")
        return False

def verify_all_files(manifest: Dict[str, Any], base_dir: Path) -> Tuple[bool, List[str]]:
    """
    Verifies all files listed in the manifest against their stored checksums.

    Args:
        manifest: The loaded manifest dictionary.
        base_dir: The base directory where files are located (e.g., data/raw).

    Returns:
        Tuple of (all_passed: bool, failed_files: List[str])
    """
    all_passed = True
    failed_files = []

    files_to_check = manifest.get("files", {})
    if not files_to_check:
        logger.warning("Manifest contains no files to verify.")
        return True, []

    for rel_path, info in files_to_check.items():
        full_path = base_dir / rel_path
        expected_checksum = info.get("checksum")

        if not full_path.exists():
            logger.error(f"File missing: {full_path}")
            all_passed = False
            failed_files.append(rel_path)
            continue

        if not verify_checksum(full_path, expected_checksum):
            all_passed = False
            failed_files.append(rel_path)

    return all_passed, failed_files

def update_checksum_for_file(file_path: Path, manifest: Dict[str, Any], algorithm: str = "sha256") -> Dict[str, Any]:
    """
    Computes the checksum for a file and updates the manifest.

    Args:
        file_path: Path to the file.
        manifest: The manifest dictionary to update.
        algorithm: Hash algorithm to use.

    Returns:
        Updated manifest dictionary.
    """
    checksum = compute_file_checksum(file_path, algorithm)
    rel_path = str(file_path.relative_to(file_path.parent.parent)) # Assuming file is in data/raw, root is parent of data

    # Ensure 'files' key exists
    if "files" not in manifest:
        manifest["files"] = {}

    manifest["files"][rel_path] = {
        "checksum": checksum,
        "algorithm": algorithm,
        "updated_at": str(Path.cwd()) # Simple timestamp placeholder or use datetime
    }
    logger.info(f"Updated checksum for {rel_path}: {checksum}")
    return manifest

def main():
    """
    Main entry point for the checksum manager.
    Demonstrates usage:
    1. Checks if data/raw exists, creates it if not.
    2. Checks for a manifest.
    3. If manifest exists, verifies all files.
    4. If manifest is missing or empty, prompts user to add files (simulated logic).
    """
    root = get_project_root()
    raw_dir = root / "data" / "raw"
    manifest_path = root / "data" / "raw" / "checksum_manifest.json"

    # Ensure directory exists
    raw_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {raw_dir}")

    # Load manifest
    manifest = load_checksum_manifest(manifest_path)

    # Check if we have files to verify
    if manifest.get("files"):
        logger.info("Found existing manifest. Verifying files...")
        passed, failed = verify_all_files(manifest, raw_dir)
        if passed:
            logger.info("All files verified successfully.")
            sys.exit(0)
        else:
            logger.error(f"Verification failed for {len(failed)} files: {failed}")
            sys.exit(1)
    else:
        logger.info("Manifest is empty or missing. "
                    "To add a file, place it in data/raw/ and run with a specific file argument "
                    "or manually update the manifest logic in a production script.")
        # In a real scenario, we might scan the directory and add new files
        # For this task, we just ensure the logic is in place and the directory exists.
        print(f"Ready to manage checksums in {raw_dir}. Manifest path: {manifest_path}")
        sys.exit(0)

if __name__ == "__main__":
    main()
