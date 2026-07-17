import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

# Ensure we can import from the project root if run as a script
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logging_config import get_logger

logger = get_logger(__name__)


def setup_output_directories():
    """Ensure the state directory exists."""
    state_dir = PROJECT_ROOT / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def calculate_file_checksum(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {e}")


def load_existing_checksums(checksum_file: Path) -> dict:
    """
    Load existing checksums from a JSON file.
    
    Args:
        checksum_file: Path to the checksums.json file.
        
    Returns:
        Dictionary of checksums, or empty dict if file doesn't exist.
    """
    if not checksum_file.exists():
        logger.info(f"Checksum file {checksum_file} does not exist. Starting fresh.")
        return {}
    
    try:
        with open(checksum_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load checksums from {checksum_file}: {e}. Starting fresh.")
        return {}


def save_checksums(checksums: dict, checksum_file: Path) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary of checksums to save.
        checksum_file: Path to the output JSON file.
    """
    try:
        with open(checksum_file, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2, sort_keys=True)
        logger.info(f"Checksums saved to {checksum_file}")
    except IOError as e:
        logger.error(f"Failed to save checksums to {checksum_file}: {e}")
        raise


def generate_checksum_for_manual_labels(state_dir: Path) -> dict:
    """
    Generate checksum for data/ground_truth/manual_labels.csv and update state/checksums.json.
    
    This function:
    1. Locates the manual_labels.csv file.
    2. Calculates its SHA-256 checksum.
    3. Loads existing checksums from state/checksums.json.
    4. Updates the entry for manual_labels.csv.
    5. Saves the updated checksums back to state/checksums.json.
    
    Returns:
        The updated checksums dictionary.
        
    Raises:
        FileNotFoundError: If manual_labels.csv does not exist.
    """
    manual_labels_path = PROJECT_ROOT / "data" / "ground_truth" / "manual_labels.csv"
    checksum_file = state_dir / "checksums.json"
    
    # Calculate the new checksum
    current_checksum = calculate_file_checksum(manual_labels_path)
    
    # Load existing checksums
    checksums = load_existing_checksums(checksum_file)
    
    # Update the entry for manual_labels.csv
    checksums["manual_labels.csv"] = {
        "sha256": current_checksum,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "file_path": str(manual_labels_path)
    }
    
    # Save the updated checksums
    save_checksums(checksums, checksum_file)
    
    logger.info(f"Generated checksum for manual_labels.csv: {current_checksum}")
    return checksums


def main():
    """Main entry point for the checksum generation script."""
    logger.info("Starting checksum generation for manual_labels.csv...")
    
    try:
        state_dir = setup_output_directories()
        checksums = generate_checksum_for_manual_labels(state_dir)
        logger.info("Checksum generation completed successfully.")
        print(f"Checksums updated in {state_dir / 'checksums.json'}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during checksum generation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
