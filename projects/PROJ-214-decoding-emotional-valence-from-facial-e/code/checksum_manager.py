"""
Checksum Manager Module for DEAP Dataset Integrity Validation.

This module implements FR-001 Part 2: Generating checksums for downloaded
dataset files and recording them in the project state file.
"""
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional

from config import ensure_directories
from state_manager import load_state, save_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum for a file.

    Args:
        file_path: Path to the file to hash

    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        raise


def generate_dataset_checksums(raw_data_dir: Path) -> Dict[str, str]:
    """
    Generate checksums for all files in the raw dataset directory.

    Args:
        raw_data_dir: Path to the data/raw directory containing dataset files

    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums
    """
    checksums = {}
    
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory does not exist: {raw_data_dir}")

    # Recursively find all files
    for file_path in raw_data_dir.rglob("*"):
        if file_path.is_file():
            # Use relative path for consistency
            relative_path = file_path.relative_to(raw_data_dir.parent)
            logger.info(f"Calculating checksum for: {relative_path}")
            checksums[str(relative_path)] = calculate_sha256(file_path)

    return checksums


def update_state_with_checksums(state_file_path: Path, checksums: Dict[str, str]) -> None:
    """
    Update the project state file with dataset checksums.

    Args:
        state_file_path: Path to the YAML state file
        checksums: Dictionary of file paths to checksums
    """
    state = load_state(state_file_path)
    
    # Initialize artifact_hashes if not present
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    
    # Update with new checksums
    state['artifact_hashes'].update(checksums)
    
    # Add metadata
    state['artifact_hashes']['_metadata'] = {
        'algorithm': 'SHA-256',
        'updated_at': state.get('last_updated', 'unknown')
    }
    
    save_state(state_file_path, state)
    logger.info(f"Updated state file with {len(checksums)} checksums")


def validate_existing_checksums(state_file_path: Path, raw_data_dir: Path) -> bool:
    """
    Validate existing checksums in state file against current files.

    Args:
        state_file_path: Path to the YAML state file
        raw_data_dir: Path to the data/raw directory

    Returns:
        True if all checksums match, False otherwise
    """
    state = load_state(state_file_path)
    
    if 'artifact_hashes' not in state:
        logger.warning("No artifact_hashes found in state file")
        return False

    stored_checksums = {k: v for k, v in state['artifact_hashes'].items() 
                      if not k.startswith('_')}
    
    if not stored_checksums:
        logger.warning("No stored checksums to validate")
        return False

    all_valid = True
    for relative_path, expected_hash in stored_checksums.items():
        file_path = raw_data_dir.parent / relative_path
        
        if not file_path.exists():
            logger.error(f"Missing file during validation: {file_path}")
            all_valid = False
            continue
        
        actual_hash = calculate_sha256(file_path)
        
        if actual_hash != expected_hash:
            logger.error(f"Checksum mismatch for {relative_path}")
            logger.error(f"  Expected: {expected_hash}")
            logger.error(f"  Actual:   {actual_hash}")
            all_valid = False
        else:
            logger.info(f"Checksum valid: {relative_path}")

    return all_valid


def main() -> None:
    """
    Main entry point for checksum generation and validation.
    
    This function:
    1. Ensures required directories exist
    2. Generates checksums for all files in data/raw
    3. Updates the project state file with the checksums
    4. Validates the checksums immediately after generation
    """
    # Ensure directories exist
    ensure_directories()
    
    # Load configuration
    from config import get_config_summary
    config = get_config_summary()
    
    # Paths
    raw_data_dir = Path(config['paths']['raw_data'])
    state_file_path = Path(config['paths']['state_file'])
    
    logger.info("Starting checksum generation for DEAP dataset")
    logger.info(f"Raw data directory: {raw_data_dir}")
    logger.info(f"State file: {state_file_path}")
    
    if not raw_data_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_data_dir}")
        logger.error("Please run download.py first to download the dataset")
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")
    
    # Check if there are any files to hash
    files = list(raw_data_dir.rglob("*"))
    files = [f for f in files if f.is_file()]
    
    if not files:
        logger.warning(f"No files found in {raw_data_dir}")
        logger.warning("Please run download.py first to download the dataset")
        raise FileNotFoundError(f"No files found in raw data directory: {raw_data_dir}")
    
    logger.info(f"Found {len(files)} files to hash")
    
    # Generate checksums
    checksums = generate_dataset_checksums(raw_data_dir)
    
    # Update state file
    update_state_with_checksums(state_file_path, checksums)
    
    # Validate immediately
    logger.info("Validating generated checksums...")
    is_valid = validate_existing_checksums(state_file_path, raw_data_dir)
    
    if is_valid:
        logger.info("✓ All checksums validated successfully")
    else:
        logger.error("✗ Checksum validation failed")
        raise RuntimeError("Checksum validation failed")
    
    logger.info("Checksum generation and validation completed successfully")


if __name__ == "__main__":
    main()
