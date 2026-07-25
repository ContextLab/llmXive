"""
Checksum utility for data integrity verification.

Computes SHA-256 checksums for files in the data directory and registers
them in the project state file.
"""
import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from utils.logging import get_logger
from utils.config import get_project_root, get_state_path

# Configure logger for this module
logger = get_logger(__name__)


def get_logger_for_module() -> logging.Logger:
    """Get logger for this module."""
    return logger


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if algorithm != "sha256":
        raise ValueError(f"Unsupported algorithm: {algorithm}. Only 'sha256' is supported.")

    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def load_state_file() -> Dict[str, Any]:
    """
    Load the project state YAML file.

    Returns:
        Dictionary containing the state file contents.
    """
    state_path = get_state_path()
    if not state_path.exists():
        logger.warning(f"State file not found at {state_path}. Creating new state.")
        return {"checksums": {}}

    try:
        import yaml
        with open(state_path, "r") as f:
            state = yaml.safe_load(f) or {}
            if "checksums" not in state:
                state["checksums"] = {}
            return state
    except Exception as e:
        logger.error(f"Failed to load state file: {e}")
        return {"checksums": {}}


def save_state_file(state: Dict[str, Any]) -> bool:
    """
    Save the project state YAML file.

    Args:
        state: Dictionary containing the state to save.

    Returns:
        True if successful, False otherwise.
    """
    state_path = get_state_path()
    try:
        import yaml
        # Ensure directory exists
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State file saved to {state_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save state file: {e}")
        return False


def register_checksum(file_path: Path, state: Dict[str, Any]) -> None:
    """
    Register a file's checksum in the state dictionary.

    Args:
        file_path: Path to the file.
        state: State dictionary to update.
    """
    checksum = compute_file_checksum(file_path)
    relative_path = file_path.relative_to(get_project_root())
    state["checksums"][str(relative_path)] = {
        "hash": checksum,
        "algorithm": "sha256"
    }
    logger.info(f"Registered checksum for {relative_path}: {checksum[:16]}...")


def scan_and_register_data_files() -> Dict[str, str]:
    """
    Scan the data directory for files and register their checksums.

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    data_path = get_project_root() / "data"
    if not data_path.exists():
        logger.warning(f"Data directory not found at {data_path}. Nothing to scan.")
        return {}

    registered_files = {}
    state = load_state_file()

    # Walk through all files in data directory
    for root, dirs, files in os.walk(data_path):
        for file in files:
            file_path = Path(root) / file
            # Skip hidden files and directories
            if file.startswith(".") or any(part.startswith(".") for part in file_path.parts):
                continue

            try:
                register_checksum(file_path, state)
                relative_path = file_path.relative_to(get_project_root())
                registered_files[str(relative_path)] = compute_file_checksum(file_path)
            except Exception as e:
                logger.error(f"Failed to process file {file_path}: {e}")

    # Save updated state
    if registered_files:
        save_state_file(state)

    return registered_files


def verify_checksum(file_path: Path, expected_hash: Optional[str] = None) -> bool:
    """
    Verify a file's checksum against an expected value or the registered value.

    Args:
        file_path: Path to the file to verify.
        expected_hash: Expected hash value. If None, uses the registered value.

    Returns:
        True if the checksum matches, False otherwise.

    Raises:
        ValueError: If no expected hash is provided and no registered hash exists.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    current_hash = compute_file_checksum(file_path)

    if expected_hash is None:
        # Try to get from state file
        state = load_state_file()
        relative_path = file_path.relative_to(get_project_root())
        if str(relative_path) not in state.get("checksums", {}):
            raise ValueError(f"No registered checksum found for {relative_path}")
        expected_hash = state["checksums"][str(relative_path)]["hash"]

    match = current_hash == expected_hash
    if match:
        logger.info(f"Checksum verified for {file_path.relative_to(get_project_root())}")
    else:
        logger.warning(f"Checksum mismatch for {file_path.relative_to(get_project_root())}. "
                     f"Expected: {expected_hash[:16]}..., Got: {current_hash[:16]}...")

    return match


def main() -> None:
    """
    Main entry point for the checksum utility.

    Scans the data directory and registers checksums for all files.
    """
    configure_logger = get_logger_for_module()
    configure_logger.info("Starting checksum utility...")

    try:
        registered = scan_and_register_data_files()
        if registered:
            logger.info(f"Successfully registered {len(registered)} files.")
            for path, hash_val in registered.items():
                logger.info(f"  {path}: {hash_val[:16]}...")
        else:
            logger.warning("No files were registered. Check if data directory exists and contains files.")
    except Exception as e:
        logger.error(f"Checksum utility failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
