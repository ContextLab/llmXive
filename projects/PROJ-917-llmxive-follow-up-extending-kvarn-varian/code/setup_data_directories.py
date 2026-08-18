"""
Script to initialize the data directory structure for the llmXive project.
Creates the required subdirectories: raw, processed, models, simulation.
"""
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
    Determine the project root directory.
    Assumes the script is run from the project root or code/ directory.
    """
    current_path = Path(__file__).resolve()
    # If running from code/, go up one level
    if current_path.name == 'setup_data_directories.py':
        return current_path.parent.parent
    return current_path.parent

def create_directories(root_dir: Path) -> List[Path]:
    """
    Create the required data directory structure.
    
    Args:
        root_dir: The project root directory.
        
    Returns:
        List of created directory paths.
    """
    data_root = root_dir / 'data'
    subdirs = ['raw', 'processed', 'models', 'simulation']
    created_dirs = []
    
    for subdir in subdirs:
        dir_path = data_root / subdir
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            logger.info(f"Created directory: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise
    
    return created_dirs

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hex digest of the file's checksum.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def record_checksums(created_dirs: List[Path], checksums: Dict[str, str]) -> Dict[str, str]:
    """
    Record checksums for the created directories (simulated as empty).
    
    Args:
        created_dirs: List of created directory paths.
        checksums: Existing checksums dictionary.
        
    Returns:
        Updated checksums dictionary.
    """
    for dir_path in created_dirs:
        # For directories, we can hash the path string as a placeholder
        # In a real scenario, we might hash the contents or metadata
        dir_hash = hashlib.sha256(str(dir_path).encode()).hexdigest()
        checksums[str(dir_path)] = dir_hash
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary of path -> checksum.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {output_path}")

def load_checksums(input_path: Path) -> Dict[str, str]:
    """
    Load checksums from a JSON file.
    
    Args:
        input_path: Path to the input JSON file.
        
    Returns:
        Dictionary of path -> checksum.
    """
    if not input_path.exists():
        return {}
    with open(input_path, 'r') as f:
        return json.load(f)

def verify_integrity(expected_checksums: Dict[str, str]) -> bool:
    """
    Verify the integrity of directories against expected checksums.
    
    Args:
        expected_checksums: Dictionary of path -> expected checksum.
        
    Returns:
        True if all directories exist and match checksums, False otherwise.
    """
    for dir_path_str, expected_hash in expected_checksums.items():
        dir_path = Path(dir_path_str)
        if not dir_path.exists():
            logger.warning(f"Directory missing: {dir_path}")
            return False
        # Re-compute hash for verification
        current_hash = hashlib.sha256(str(dir_path).encode()).hexdigest()
        if current_hash != expected_hash:
            logger.warning(f"Checksum mismatch for {dir_path}")
            return False
    return True

def main() -> None:
    """
    Main entry point for the data directory setup script.
    """
    logger.info("Starting data directory initialization...")
    
    project_root = get_project_root()
    logger.info(f"Project root identified as: {project_root}")
    
    try:
        created_dirs = create_directories(project_root)
        logger.info(f"Successfully created {len(created_dirs)} directories.")
        
        # Record checksums for the created directories
        checksums = {}
        checksums = record_checksums(created_dirs, checksums)
        
        # Save checksums to a file in the data directory
        checksum_file = project_root / 'data' / '.checksums.json'
        save_checksums(checksums, checksum_file)
        
        # Verification step
        loaded_checksums = load_checksums(checksum_file)
        if verify_integrity(loaded_checksums):
            logger.info("Directory structure verification passed.")
        else:
            logger.warning("Directory structure verification failed.")
            
    except Exception as e:
        logger.error(f"Failed to initialize data directories: {e}")
        sys.exit(1)
    
    logger.info("Data directory initialization completed successfully.")

if __name__ == '__main__':
    main()
