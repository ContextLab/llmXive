"""
Setup data directories with .gitkeep files and checksum management.
This module handles the creation of required directory structures and
generates checksums for data integrity verification.
"""
import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import existing utilities from the project
from config import compute_file_checksum, compute_directory_checksum, save_checksums, load_checksums, verify_checksums, ensure_dirs
from utils import setup_logger, get_logger, PipelineError

def create_gitkeep(directory_path: Path) -> None:
    """
    Create a .gitkeep file in the specified directory to ensure it is tracked by git.
    
    Args:
        directory_path: Path to the directory where .gitkeep should be created
    """
    gitkeep_path = directory_path / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.write_text("# Keep this directory under version control\n")
        logging.info(f"Created .gitkeep in {directory_path}")
    else:
        logging.debug(f".gitkeep already exists in {directory_path}")

def setup_data_directories(base_path: Path) -> Dict[str, Path]:
    """
    Create the required data directory structure.
    
    Args:
        base_path: Base project root path
        
    Returns:
        Dictionary mapping directory names to their absolute paths
    """
    data_root = base_path / "data"
    raw_data = data_root / "raw"
    processed_data = data_root / "processed"
    logs_data = data_root / "logs"
    
    directories = {
        "raw": raw_data,
        "processed": processed_data,
        "logs": logs_data
    }
    
    for name, path in directories.items():
        ensure_dirs(path)
        create_gitkeep(path)
        logging.info(f"Set up directory: {path}")
    
    return directories

def generate_checksums(data_root: Path, checksum_file: Optional[Path] = None) -> Dict[str, str]:
    """
    Generate checksums for all files in the data directories.
    
    Args:
        data_root: Root directory of the data folder
        checksum_file: Optional path to save checksums (defaults to data_root/checksums.json)
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums
    """
    if checksum_file is None:
        checksum_file = data_root / "checksums.json"
    
    logging.info(f"Generating checksums for {data_root}")
    
    # Collect all files
    files = []
    for root, dirs, filenames in os.walk(data_root):
        # Skip .gitkeep files
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for filename in filenames:
            if filename == ".gitkeep":
                continue
            filepath = Path(root) / filename
            files.append(filepath)
    
    # Compute checksums
    checksums = {}
    for filepath in files:
        try:
            checksum = compute_file_checksum(filepath)
            rel_path = filepath.relative_to(data_root)
            checksums[str(rel_path)] = checksum
            logging.debug(f"Checksum for {rel_path}: {checksum}")
        except Exception as e:
            logging.warning(f"Could not compute checksum for {filepath}: {e}")
    
    # Save checksums
    save_checksums(checksums, checksum_file)
    logging.info(f"Checksums saved to {checksum_file}")
    
    return checksums

def verify_checksums(data_root: Path, checksum_file: Optional[Path] = None) -> bool:
    """
    Verify all files in data directories against stored checksums.
    
    Args:
        data_root: Root directory of the data folder
        checksum_file: Optional path to checksums file (defaults to data_root/checksums.json)
        
    Returns:
        True if all checksums verify, False otherwise
    """
    if checksum_file is None:
        checksum_file = data_root / "checksums.json"
    
    if not checksum_file.exists():
        logging.error(f"Checksum file not found: {checksum_file}")
        return False
    
    logging.info(f"Verifying checksums from {checksum_file}")
    return verify_checksums(checksum_file, data_root)

def main():
    """
    Main entry point for setting up data directories and checksums.
    
    This function:
    1. Creates data/raw, data/processed, data/logs directories
    2. Adds .gitkeep files to each directory
    3. Generates initial checksums for existing data files
    4. Provides verification capability
    """
    # Setup logging
    logger = setup_logger("setup_data_dirs")
    
    # Determine base path
    base_path = Path(__file__).resolve().parent.parent
    if not (base_path / "data").exists():
        logger.warning(f"Data directory not found at {base_path / 'data'}, creating structure...")
    
    # Setup directories
    directories = setup_data_directories(base_path)
    
    # Generate checksums for existing files
    data_root = base_path / "data"
    if data_root.exists():
        generate_checksums(data_root)
    else:
        logger.info("No existing data files to checksum.")
    
    # Summary
    logger.info("Data directory setup complete.")
    logger.info(f"Directories created: {list(directories.keys())}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
