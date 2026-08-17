"""
Setup script to initialize the data directory structure for the llmXive project.
Creates the required subdirectories under 'data/' for raw, processed, models, and simulation artifacts.
"""
import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the script is run from the project root or code/ directory.
    """
    current = Path(__file__).resolve()
    # Traverse up until we find a 'data' directory or hit the filesystem root
    for parent in current.parents:
        if (parent / 'data').exists() or parent.name == 'PROJ-917-llmxive-follow-up-extending-kvarn-varian':
            return parent
    # Fallback: assume current working directory is root if structure isn't detected
    return Path.cwd()


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
    For directories, we compute a hash of the sorted list of files.
    """
    if not file_path.exists():
        return ""
    
    if file_path.is_file():
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    elif file_path.is_dir():
        # For directories, we hash the sorted list of relative paths
        files = []
        for p in sorted(file_path.rglob('*')):
            if p.is_file():
                rel_path = p.relative_to(file_path)
                files.append(str(rel_path))
        content = "\n".join(files).encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    return ""


def record_checksums(root_dir: Path, created_dirs: List[Path]) -> Dict[str, Any]:
    """
    Record checksums for the created directories to ensure integrity.
    """
    checksums = {}
    for dir_path in created_dirs:
        checksum = compute_file_checksum(dir_path)
        rel_path = dir_path.relative_to(root_dir)
        checksums[str(rel_path)] = checksum
    return checksums


def save_checksums(checksums: Dict[str, Any], output_path: Path) -> None:
    """
    Save checksums to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {output_path}")


def load_checksums(input_path: Path) -> Dict[str, Any]:
    """
    Load checksums from a JSON file.
    """
    if not input_path.exists():
        return {}
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def verify_integrity(root_dir: Path, expected_checksums: Dict[str, Any]) -> bool:
    """
    Verify the integrity of the data directories against stored checksums.
    """
    is_valid = True
    for rel_path_str, expected_hash in expected_checksums.items():
        dir_path = root_dir / rel_path_str
        if not dir_path.exists():
            logger.warning(f"Directory missing: {dir_path}")
            is_valid = False
            continue
        
        actual_hash = compute_file_checksum(dir_path)
        if actual_hash != expected_hash:
            logger.warning(f"Checksum mismatch for {dir_path}: expected {expected_hash}, got {actual_hash}")
            is_valid = False
        else:
            logger.info(f"Verified: {dir_path}")
    
    return is_valid


def main() -> int:
    """
    Main entry point for the setup script.
    """
    root_dir = get_project_root()
    logger.info(f"Project root identified as: {root_dir}")
    
    try:
        created_dirs = create_directories(root_dir)
        
        if not created_dirs:
            logger.error("No directories were created.")
            return 1
        
        # Record checksums immediately after creation
        checksums = record_checksums(root_dir, created_dirs)
        checksum_file = root_dir / 'data' / '.directory_checksums.json'
        save_checksums(checksums, checksum_file)
        
        logger.info("Data directory structure initialization complete.")
        return 0
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
