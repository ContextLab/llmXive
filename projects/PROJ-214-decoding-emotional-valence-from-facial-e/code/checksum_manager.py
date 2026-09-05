import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional

from config import ensure_directories
from state_manager import load_state, save_state

logger = logging.getLogger(__name__)


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files without memory issues
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"Cannot calculate checksum: file not found at {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error calculating checksum for {file_path}: {e}")


def generate_dataset_checksums(data_dir: Path) -> Dict[str, str]:
    """
    Generate checksums for all files in the raw data directory.

    Args:
        data_dir: Path to the directory containing dataset files.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums.
    """
    checksums = {}
    data_dir = Path(data_dir)

    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory does not exist: {data_dir}")

    # Walk through all files in the directory
    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(data_dir)
            try:
                checksum = calculate_sha256(file_path)
                checksums[str(rel_path)] = checksum
                logger.info(f"Checksum generated for {rel_path}: {checksum}")
            except Exception as e:
                logger.error(f"Failed to generate checksum for {rel_path}: {e}")

    return checksums


def update_state_with_checksums(checksums: Dict[str, str]) -> bool:
    """
    Update the project state file with dataset checksums.

    Args:
        checksums: Dictionary of file paths to checksums.

    Returns:
        True if successful, False otherwise.
    """
    try:
        state = load_state()
        
        # Ensure the artifact_hashes key exists
        if "artifact_hashes" not in state:
            state["artifact_hashes"] = {}
        
        # Update with new checksums
        state["artifact_hashes"]["dataset_files"] = checksums
        
        # Add metadata about when this was generated
        from datetime import datetime
        state["artifact_hashes"]["last_updated"] = datetime.now().isoformat()
        
        save_state(state)
        logger.info("State file updated with dataset checksums successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to update state with checksums: {e}")
        return False


def validate_existing_checksums() -> Dict[str, bool]:
    """
    Validate existing checksums in the state file against current files.

    Returns:
        Dictionary mapping file paths to validation status (True if valid).
    """
    state = load_state()
    
    if "artifact_hashes" not in state or "dataset_files" not in state["artifact_hashes"]:
        logger.warning("No existing checksums found in state file.")
        return {}
    
    stored_checksums = state["artifact_hashes"]["dataset_files"]
    validation_results = {}
    data_dir = Path("data/raw")
    
    for rel_path, stored_hash in stored_checksums.items():
        file_path = data_dir / rel_path
        if file_path.exists():
            try:
                current_hash = calculate_sha256(file_path)
                is_valid = current_hash == stored_hash
                validation_results[rel_path] = is_valid
                status = "VALID" if is_valid else "INVALID"
                logger.info(f"Validation for {rel_path}: {status}")
            except Exception as e:
                logger.error(f"Error validating {rel_path}: {e}")
                validation_results[rel_path] = False
        else:
            logger.warning(f"File not found during validation: {rel_path}")
            validation_results[rel_path] = False
    
    return validation_results


def main():
    """
    Main entry point for checksum generation and validation.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ensure directories exist
    ensure_directories()
    
    data_dir = Path("data/raw")
    
    if not data_dir.exists() or not any(data_dir.iterdir()):
        logger.warning(f"Data directory is empty or does not exist: {data_dir}")
        logger.info("Please run download.py first to fetch the dataset.")
        return
    
    logger.info("Generating checksums for dataset files...")
    checksums = generate_dataset_checksums(data_dir)
    
    if not checksums:
        logger.warning("No checksums generated. Check if files exist in data/raw.")
        return
    
    logger.info(f"Generated {len(checksums)} checksums.")
    
    logger.info("Updating state file...")
    success = update_state_with_checksums(checksums)
    
    if success:
        logger.info("Checksum generation and state update completed successfully.")
        
        # Optionally validate existing checksums
        logger.info("Validating existing checksums...")
        validation_results = validate_existing_checksums()
        if validation_results:
            valid_count = sum(validation_results.values())
            logger.info(f"Validation complete: {valid_count}/{len(validation_results)} files valid.")
    else:
        logger.error("Failed to update state file with checksums.")


if __name__ == "__main__":
    main()
