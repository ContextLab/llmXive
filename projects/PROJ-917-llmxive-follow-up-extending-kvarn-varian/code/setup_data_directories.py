import os
import sys
from pathlib import Path
import hashlib
import json
from typing import Dict, Any, Optional, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """
    Returns the project root directory.
    Assumes the script is run from the project root or code/ directory.
    """
    current_path = Path.cwd()
    if current_path.name == 'code':
        return current_path.parent
    return current_path

def create_directories() -> bool:
    """
    Creates the required directory structure for the project.
    Specifically targets the data/ directory tree as per T001b.
    
    Structure:
    data/
      raw/
      processed/
      results/
      models/
      
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    project_root = get_project_root()
    data_root = project_root / 'data'
    
    required_dirs = [
        data_root / 'raw',
        data_root / 'processed',
        data_root / 'results',
        data_root / 'models',
        # Additional directories often needed for the pipeline
        data_root / 'figures',
        data_root / 'analysis'
    ]
    
    success = True
    for directory in required_dirs:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        except OSError as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            success = False
    
    return success

def compute_file_checksum(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    
    Args:
        file_path (Path): Path to the file.
        
    Returns:
        str: Hexadecimal checksum string.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return ""

def record_checksums(checksums: Dict[str, str]) -> Dict[str, Any]:
    """
    Records checksums into a data structure.
    
    Args:
        checksums (Dict[str, str]): Dictionary of file paths and checksums.
        
    Returns:
        Dict[str, Any]: Updated checksum record.
    """
    return {
        "files": checksums,
        "status": "verified"
    }

def save_checksums(checksum_data: Dict[str, Any], output_path: Path) -> bool:
    """
    Saves checksum data to a JSON file.
    
    Args:
        checksum_data (Dict[str, Any]): The data to save.
        output_path (Path): Path to the output JSON file.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(checksum_data, f, indent=2)
        logger.info(f"Checksums saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save checksums: {e}")
        return False

def load_checksums(input_path: Path) -> Optional[Dict[str, Any]]:
    """
    Loads checksum data from a JSON file.
    
    Args:
        input_path (Path): Path to the input JSON file.
        
    Returns:
        Optional[Dict[str, Any]]: The loaded data or None if failed.
    """
    try:
        with open(input_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Checksum file not found: {input_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse checksum file {input_path}: {e}")
        return None

def verify_integrity(checksums: Dict[str, str]) -> bool:
    """
    Verifies the integrity of files against stored checksums.
    
    Args:
        checksums (Dict[str, str]): Dictionary of expected file checksums.
        
    Returns:
        bool: True if all files match, False otherwise.
    """
    all_valid = True
    for file_path_str, expected_hash in checksums.items():
        file_path = Path(file_path_str)
        if not file_path.exists():
            logger.error(f"File missing for integrity check: {file_path}")
            all_valid = False
            continue
        
        actual_hash = compute_file_checksum(file_path)
        if actual_hash != expected_hash:
            logger.error(f"Integrity check failed for {file_path}")
            all_valid = False
        else:
            logger.info(f"Integrity check passed for {file_path}")
    
    return all_valid

def main() -> int:
    """
    Main entry point for the data directory setup script.
    
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    logger.info("Starting data directory initialization...")
    
    if create_directories():
        logger.info("Data directory structure created successfully.")
        return 0
    else:
        logger.error("Failed to create some data directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
