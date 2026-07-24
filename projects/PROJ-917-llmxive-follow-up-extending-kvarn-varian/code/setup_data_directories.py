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

def create_directories(base_path: Optional[Path] = None) -> Path:
    """
    Creates the required directory structure for the llmXive project.
    
    Args:
        base_path: Optional base path. Defaults to current working directory.
        
    Returns:
        The base Path object used.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    # Define the required directory structure relative to base_path
    # Based on tasks.md: data/ generated, models, simulation, analysis
    sub_dirs = [
        "data/generated",
        "data/models",
        "data/simulation",
        "data/analysis",
        # Also create state/ for checksums as referenced in T001d
        "state"
    ]
    
    created_paths = []
    for sub_dir in sub_dirs:
        full_path = base_path / sub_dir
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(full_path)
            logger.info(f"Created directory: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise
    
    logger.info(f"Successfully created {len(created_paths)} directories.")
    return base_path

def compute_file_checksum(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def record_checksums(base_path: Path, files: List[Path]) -> Dict[str, str]:
    """
    Records checksums for a list of files relative to base_path.
    
    Args:
        base_path: The root path for relative paths.
        files: List of file paths to checksum.
        
    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    checksums = {}
    for file_path in files:
        if file_path.exists():
            rel_path = str(file_path.relative_to(base_path))
            checksum = compute_file_checksum(file_path)
            checksums[rel_path] = checksum
            logger.debug(f"Checksum recorded for {rel_path}: {checksum}")
        else:
            logger.warning(f"File not found, skipping checksum: {file_path}")
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Saves the checksum dictionary to a JSON file.
    
    Args:
        checksums: Dictionary of checksums.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {output_path}")

def load_checksums(input_path: Path) -> Dict[str, str]:
    """
    Loads checksums from a JSON file.
    
    Args:
        input_path: Path to the input JSON file.
        
    Returns:
        Dictionary of checksums.
    """
    with open(input_path, 'r') as f:
        return json.load(f)

def verify_integrity(base_path: Path, checksums_file: Path) -> bool:
    """
    Verifies the integrity of files against stored checksums.
    
    Args:
        base_path: The root path for relative paths.
        checksums_file: Path to the JSON file containing stored checksums.
        
    Returns:
        True if all files match their checksums, False otherwise.
    """
    if not checksums_file.exists():
        logger.error(f"Checksums file not found: {checksums_file}")
        return False
    
    stored_checksums = load_checksums(checksums_file)
    all_valid = True
    
    for rel_path, stored_hash in stored_checksums.items():
        file_path = base_path / rel_path
        if file_path.exists():
            current_hash = compute_file_checksum(file_path)
            if current_hash != stored_hash:
                logger.error(f"Integrity check failed for {rel_path}")
                all_valid = False
            else:
                logger.debug(f"Integrity check passed for {rel_path}")
        else:
            logger.warning(f"File missing during integrity check: {rel_path}")
            all_valid = False
            
    return all_valid

def main():
    """
    Main entry point to create data directories and optionally manage checksums.
    For T001b, this primarily creates the directory structure.
    """
    base_path = Path.cwd()
    logger.info(f"Starting directory setup in: {base_path}")
    
    try:
        create_directories(base_path)
        logger.info("Directory creation completed successfully.")
        
        # T001b specific deliverable: Directories created.
        # We log the specific paths created for verification.
        data_dirs = [
            base_path / "data" / "generated",
            base_path / "data" / "models",
            base_path / "data" / "simulation",
            base_path / "data" / "analysis"
        ]
        
        for d in data_dirs:
            if d.exists() and d.is_dir():
                logger.info(f"Verified existence: {d}")
            else:
                logger.error(f"Missing expected directory: {d}")
                return 1
                
        return 0
        
    except Exception as e:
        logger.critical(f"Setup failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())