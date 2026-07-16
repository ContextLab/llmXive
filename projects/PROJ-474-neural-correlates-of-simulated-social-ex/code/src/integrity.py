"""
Data integrity checker module.

Provides functionality to compute SHA-256 hashes for files in the data/ directory
and store/manage these hashes in the state/ directory.
"""
import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from src.utils import get_logger, PipelineError

logger = get_logger(__name__)

# Default paths relative to project root
DEFAULT_DATA_DIR = "data"
DEFAULT_STATE_DIR = "state"
HASH_STORE_FILENAME = "data_hashes.json"

class IntegrityError(PipelineError):
    """Custom exception for integrity check failures."""
    pass


def compute_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read at a time for large files.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


def scan_data_directory(data_dir: Path) -> List[Path]:
    """
    Recursively scan the data directory for all files.

    Args:
        data_dir: Path to the data directory.

    Returns:
        List of Path objects for all files found.
    """
    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        return []
    
    files = []
    for root, _, filenames in os.walk(data_dir):
        for filename in filenames:
            files.append(Path(root) / filename)
    
    logger.info(f"Found {len(files)} files in {data_dir}")
    return files


def generate_hashes(data_dir: Path = Path(DEFAULT_DATA_DIR)) -> Dict[str, str]:
    """
    Generate SHA-256 hashes for all files in the data directory.

    Args:
        data_dir: Path to the data directory.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    hashes = {}
    files = scan_data_directory(data_dir)
    
    for file_path in files:
        try:
            relative_path = str(file_path.relative_to(data_dir))
            file_hash = compute_file_hash(file_path)
            hashes[relative_path] = file_hash
            logger.debug(f"Hashed: {relative_path}")
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            # Continue with other files instead of failing the whole process
    
    return hashes


def get_state_path(state_dir: Path = Path(DEFAULT_STATE_DIR)) -> Path:
    """
    Ensure the state directory exists and return the path to the hash store file.

    Args:
        state_dir: Path to the state directory.

    Returns:
        Path to the hash store JSON file.
    """
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / HASH_STORE_FILENAME


def save_hashes(hashes: Dict[str, str], state_dir: Path = Path(DEFAULT_STATE_DIR)) -> Path:
    """
    Save the computed hashes to the state directory.

    Args:
        hashes: Dictionary of relative paths to hashes.
        state_dir: Path to the state directory.

    Returns:
        Path to the saved hash store file.
    """
    hash_store_path = get_state_path(state_dir)
    try:
        with open(hash_store_path, 'w', encoding='utf-8') as f:
            json.dump(hashes, f, indent=2, sort_keys=True)
        logger.info(f"Saved {len(hashes)} hashes to {hash_store_path}")
        return hash_store_path
    except IOError as e:
        logger.error(f"Failed to save hashes to {hash_store_path}: {e}")
        raise IntegrityError(f"Could not save hash store: {e}")


def load_hashes(state_dir: Path = Path(DEFAULT_STATE_DIR)) -> Dict[str, str]:
    """
    Load previously saved hashes from the state directory.

    Args:
        state_dir: Path to the state directory.

    Returns:
        Dictionary of relative paths to hashes, or empty dict if file not found.

    Raises:
        IntegrityError: If the hash store file exists but is malformed.
    """
    hash_store_path = get_state_path(state_dir)
    
    if not hash_store_path.exists():
        logger.warning(f"No existing hash store found at {hash_store_path}")
        return {}
    
    try:
        with open(hash_store_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Malformed JSON in hash store: {e}")
        raise IntegrityError(f"Corrupt hash store file: {hash_store_path}")
    except IOError as e:
        logger.error(f"Failed to read hash store: {e}")
        raise IntegrityError(f"Could not read hash store: {e}")


def verify_integrity(
    data_dir: Path = Path(DEFAULT_DATA_DIR),
    state_dir: Path = Path(DEFAULT_STATE_DIR),
    strict: bool = False
) -> Dict[str, str]:
    """
    Verify current data files against stored hashes.

    Args:
        data_dir: Path to the data directory.
        state_dir: Path to the state directory.
        strict: If True, raise an error on any mismatch. If False, return mismatches.

    Returns:
        Dictionary of relative paths to their current hashes.
        If mismatches exist and strict=False, mismatches are logged.

    Raises:
        IntegrityError: If strict=True and any mismatches or missing files are found.
    """
    stored_hashes = load_hashes(state_dir)
    current_hashes = generate_hashes(data_dir)
    mismatches = {}
    missing_files = []
    new_files = []

    # Check for missing files (in stored but not in current)
    for rel_path in stored_hashes:
        if rel_path not in current_hashes:
            missing_files.append(rel_path)
    
    # Check for new files (in current but not in stored)
    for rel_path in current_hashes:
        if rel_path not in stored_hashes:
            new_files.append(rel_path)

    # Check for hash mismatches
    for rel_path, stored_hash in stored_hashes.items():
        if rel_path in current_hashes:
            if stored_hash != current_hashes[rel_path]:
                mismatches[rel_path] = {
                    "stored": stored_hash,
                    "current": current_hashes[rel_path]
                }

    # Report results
    if missing_files:
        logger.warning(f"Missing {len(missing_files)} files that were previously hashed")
        for f in missing_files:
            logger.warning(f"  Missing: {f}")
    
    if new_files:
        logger.info(f"Found {len(new_files)} new files not in hash store")
        for f in new_files:
            logger.info(f"  New: {f}")

    if mismatches:
        logger.error(f"Found {len(mismatches)} files with hash mismatches")
        for f, details in mismatches.items():
            logger.error(f"  Mismatch: {f}")
            logger.error(f"    Stored:  {details['stored']}")
            logger.error(f"    Current: {details['current']}")
        
        if strict:
            raise IntegrityError(f"Data integrity check failed: {len(mismatches)} mismatches found")
    
    if not stored_hashes and not current_hashes:
        logger.warning("No data files found to verify")
    elif not stored_hashes and current_hashes:
        logger.info("No stored hashes found; consider running 'generate' first")

    return current_hashes


def update_hashes(
    data_dir: Path = Path(DEFAULT_DATA_DIR),
    state_dir: Path = Path(DEFAULT_STATE_DIR)
) -> Dict[str, str]:
    """
    Generate new hashes and update the stored hash file.

    This is a convenience function that combines generate_hashes and save_hashes.

    Args:
        data_dir: Path to the data directory.
        state_dir: Path to the state directory.

    Returns:
        Dictionary of relative paths to their new hashes.
    """
    logger.info("Updating data integrity hashes...")
    hashes = generate_hashes(data_dir)
    save_hashes(hashes, state_dir)
    return hashes


def main():
    """
    Command-line interface for the integrity checker.

    Usage:
        python -m src.integrity [command]
        
    Commands:
        generate  - Generate hashes for all files in data/ and save to state/
        verify    - Verify data files against stored hashes
        update    - Alias for generate (update stored hashes)
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.integrity [generate|verify|update]")
        print("  generate: Scan data/ and save hashes to state/")
        print("  verify:   Compare data/ files against stored hashes")
        print("  update:   Alias for generate")
        sys.exit(1)

    command = sys.argv[1].lower()
    data_dir = Path(DEFAULT_DATA_DIR)
    state_dir = Path(DEFAULT_STATE_DIR)

    try:
        if command == "generate" or command == "update":
            hashes = update_hashes(data_dir, state_dir)
            print(f"Successfully hashed {len(hashes)} files.")
        elif command == "verify":
            hashes = verify_integrity(data_dir, state_dir, strict=True)
            print(f"Verification passed. {len(hashes)} files checked.")
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except IntegrityError as e:
        print(f"Integrity check failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during integrity check")
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
