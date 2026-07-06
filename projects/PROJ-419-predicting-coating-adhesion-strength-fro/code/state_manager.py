"""
State management module for tracking raw data file checksums.
Implements Constitution Principle III: Data provenance and integrity.
"""
import os
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

STATE_FILE_PATH = "state/data_checksums.yaml"
RAW_DATA_DIR = "data/raw"

def calculate_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal checksum string.
    """
    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum calculation: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        raise

def scan_raw_data_directory(directory: str = RAW_DATA_DIR) -> List[str]:
    """
    Scan the raw data directory for all files.

    Args:
        directory: Path to the raw data directory.

    Returns:
        List of relative file paths found in the directory.
    """
    path = Path(directory)
    if not path.exists():
        logger.warning(f"Raw data directory does not exist: {directory}")
        return []

    files = []
    for file_path in path.rglob("*"):
        if file_path.is_file():
            # Store relative path from project root
            rel_path = str(file_path.relative_to(Path.cwd()))
            files.append(rel_path)
    
    logger.info(f"Found {len(files)} files in {directory}")
    return files

def generate_state_checksums(files: Optional[List[str]] = None) -> Dict:
    """
    Generate a dictionary of checksums for a list of files.

    Args:
        files: List of file paths. If None, scans RAW_DATA_DIR.

    Returns:
        Dictionary with file paths as keys and checksums as values.
    """
    if files is None:
        files = scan_raw_data_directory()

    checksums = {}
    for file_path in files:
        try:
            checksum = calculate_file_checksum(file_path)
            checksums[file_path] = {
                "checksum": checksum,
                "algorithm": "sha256",
                "status": "verified"
            }
            logger.debug(f"Checksum generated for {file_path}: {checksum[:16]}...")
        except Exception as e:
            logger.warning(f"Failed to checksum {file_path}: {e}")
            checksums[file_path] = {
                "checksum": None,
                "algorithm": "sha256",
                "status": "error",
                "error": str(e)
            }
    
    return checksums

def write_state_file(checksums: Dict, output_path: str = STATE_FILE_PATH) -> None:
    """
    Write the checksums dictionary to a YAML state file.

    Args:
        checksums: Dictionary of checksums.
        output_path: Path to the output YAML file.
    """
    state_dir = os.path.dirname(output_path)
    if state_dir and not os.path.exists(state_dir):
        os.makedirs(state_dir)
        logger.info(f"Created state directory: {state_dir}")

    state_data = {
        "version": "1.0",
        "generated_at": None, # Set by caller or external tool if needed
        "raw_data_checksums": checksums
    }

    # Add a timestamp for traceability
    import datetime
    state_data["generated_at"] = datetime.datetime.now().isoformat()

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"State file written to {output_path}")

def verify_state_checksums(state_path: str = STATE_FILE_PATH) -> bool:
    """
    Verify the current checksums of files against the stored state.

    Args:
        state_path: Path to the state YAML file.

    Returns:
        True if all checksums match, False otherwise.
    """
    if not os.path.exists(state_path):
        logger.error(f"State file not found: {state_path}")
        return False

    with open(state_path, "r", encoding="utf-8") as f:
        state_data = yaml.safe_load(f)

    stored_checksums = state_data.get("raw_data_checksums", {})
    all_valid = True

    for file_path, info in stored_checksums.items():
        if not os.path.exists(file_path):
            logger.warning(f"File missing during verification: {file_path}")
            all_valid = False
            continue

        current_checksum = calculate_file_checksum(file_path)
        stored_checksum = info.get("checksum")

        if current_checksum != stored_checksum:
            logger.error(f"Checksum mismatch for {file_path}: "
                         f"expected {stored_checksum}, got {current_checksum}")
            all_valid = False
        else:
            logger.debug(f"Checksum verified for {file_path}")

    return all_valid

def main() -> None:
    """
    Main entry point to generate/update state checksums.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    logger.info("Starting state checksum generation...")
    
    # Scan for raw data files
    files = scan_raw_data_directory()
    if not files:
        logger.warning("No files found in raw data directory. State file will be empty.")
    
    # Generate checksums
    checksums = generate_state_checksums(files)
    
    # Write state file
    write_state_file(checksums)
    
    logger.info("State checksum generation completed.")

if __name__ == "__main__":
    main()
