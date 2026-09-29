import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Ensure logging is configured before use
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """
    Returns the root directory of the project (the 'code' directory).
    Assumes the script is run from within 'code' or a subdirectory.
    """
    current = Path(__file__).resolve()
    # Traverse up to find the 'code' directory which contains 'src'
    # If running as a module, __file__ is relative to the package root.
    # We look for the directory named 'code' that contains 'src'.
    while current != current.parent:
        if current.name == "code" and (current / "src").exists():
            return current
        current = current.parent
    # Fallback: assume current working directory is the root if structure is flat
    return Path.cwd()

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Computes the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default 'sha256').

    Returns:
        Hexadecimal string of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

    return hash_func.hexdigest()

def load_checksum_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Loads the checksum manifest JSON file.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Dictionary containing the manifest data.

    Raises:
        FileNotFoundError: If manifest does not exist.
        json.JSONDecodeError: If manifest is invalid JSON.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Checksum manifest not found: {manifest_path}")

    with open(manifest_path, "r") as f:
        return json.load(f)

def save_checksum_manifest(manifest_path: Path, data: Dict[str, Any]) -> None:
    """
    Saves the checksum manifest to a JSON file.

    Args:
        manifest_path: Path to save the manifest.
        data: Dictionary containing the manifest data.
    """
    # Ensure directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Checksum manifest saved to {manifest_path}")

def verify_checksum(file_path: Path, expected_checksum: str, algorithm: str = "sha256") -> Tuple[bool, str]:
    """
    Verifies the checksum of a file against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected checksum string.
        algorithm: Hash algorithm to use.

    Returns:
        Tuple of (is_valid, computed_checksum).
    """
    computed = compute_file_checksum(file_path, algorithm)
    is_valid = computed == expected_checksum
    return is_valid, computed

def verify_all_files(manifest_path: Path) -> Dict[str, bool]:
    """
    Verifies all files listed in the manifest against their stored checksums.

    Args:
        manifest_path: Path to the checksum manifest.

    Returns:
        Dictionary mapping file paths to verification status (True/False).
    """
    manifest = load_checksum_manifest(manifest_path)
    results = {}
    project_root = get_project_root()

    for file_rel_path, file_info in manifest.get("files", {}).items():
        full_path = project_root / file_rel_path
        if not full_path.exists():
            logger.warning(f"File missing: {full_path}")
            results[file_rel_path] = False
            continue

        expected = file_info.get("checksum")
        is_valid, _ = verify_checksum(full_path, expected)
        results[file_rel_path] = is_valid

        status = "OK" if is_valid else "MISMATCH"
        logger.info(f"Verification {status}: {file_rel_path}")

    return results

def update_checksum_for_file(file_path: Path, manifest_path: Path) -> None:
    """
    Updates the checksum for a specific file in the manifest.

    Args:
        file_path: Path to the file to update.
        manifest_path: Path to the manifest file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot update checksum: file not found {file_path}")

    # Load existing manifest or create new
    if manifest_path.exists():
        manifest = load_checksum_manifest(manifest_path)
    else:
        manifest = {"files": {}, "metadata": {"created": "now", "updated": "now"}}

    # Compute new checksum
    checksum = compute_file_checksum(file_path)
    rel_path = str(file_path.relative_to(get_project_root()))

    manifest["files"][rel_path] = {
        "checksum": checksum,
        "algorithm": "sha256",
        "size_bytes": file_path.stat().st_size
    }

    save_checksum_manifest(manifest_path, manifest)
    logger.info(f"Updated checksum for {rel_path}")

def main():
    """
    CLI entry point for checksum management.
    Usage:
      python -m src.data.checksum_manager init
      python -m src.data.checksum_manager update <file_path>
      python -m src.data.checksum_manager verify
    """
    if len(sys.argv) < 2:
        print("Usage: python -m src.data.checksum_manager <command> [args]")
        print("Commands: init, update <file>, verify")
        sys.exit(1)

    command = sys.argv[1]
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    manifest_path = raw_dir / ".checksums.json"

    if command == "init":
        # Initialize manifest if raw directory exists
        if raw_dir.exists():
            # Find all files in data/raw
            files = {}
            for file_path in raw_dir.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith("."):
                    rel_path = str(file_path.relative_to(project_root))
                    try:
                        checksum = compute_file_checksum(file_path)
                        files[rel_path] = {
                            "checksum": checksum,
                            "algorithm": "sha256",
                            "size_bytes": file_path.stat().st_size
                        }
                    except Exception as e:
                        logger.error(f"Failed to compute checksum for {file_path}: {e}")

            if files:
                manifest = {"files": files, "metadata": {"created": "init"}}
                save_checksum_manifest(manifest_path, manifest)
                logger.info(f"Initialized checksum manifest with {len(files)} files.")
            else:
                logger.warning("No files found in data/raw to initialize manifest.")
        else:
            logger.error(f"Directory {raw_dir} does not exist. Cannot initialize.")

    elif command == "update":
        if len(sys.argv) < 3:
            print("Usage: python -m src.data.checksum_manager update <file_path>")
            sys.exit(1)
        file_path = Path(sys.argv[2])
        if not file_path.is_absolute():
            file_path = project_root / file_path
        update_checksum_for_file(file_path, manifest_path)

    elif command == "verify":
        if not manifest_path.exists():
            logger.error("Manifest not found. Run 'init' first.")
            sys.exit(1)
        results = verify_all_files(manifest_path)
        failed = [k for k, v in results.items() if not v]
        if failed:
            logger.error(f"Verification failed for {len(failed)} files: {failed}")
            sys.exit(1)
        else:
            logger.info("All files verified successfully.")
            sys.exit(0)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
