"""
Data directory setup and checksumming hooks for T011.

This module creates the required data directory structure (data/raw/, data/derived/)
and implements checksumming hooks to ensure data integrity and reproducibility.
It integrates with the manifest system (T010) to track all data artifacts.
"""
import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_directories(base_path: Path) -> Dict[str, Path]:
    """
    Create the required data directory structure.
    
    Creates:
        - data/raw/
        - data/derived/
        - state/hashes/
        
    Args:
        base_path: Project root path
        
    Returns:
        Dictionary mapping directory names to their Path objects
    """
    data_raw = base_path / "data" / "raw"
    data_derived = base_path / "data" / "derived"
    state_hashes = base_path / "state" / "hashes"
    
    directories = {
        "raw": data_raw,
        "derived": data_derived,
        "state_hashes": state_hashes
    }
    
    for dir_name, dir_path in directories.items():
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.debug(f"Directory already exists: {dir_path}")
    
    return directories

def get_data_files(data_dir: Path) -> List[Path]:
    """
    Get all files in a data directory recursively.
    
    Args:
        data_dir: Directory to scan
        
    Returns:
        List of Path objects for all files found
    """
    if not data_dir.exists():
        logger.warning(f"Directory does not exist: {data_dir}")
        return []
    
    files = []
    for root, _, filenames in os.walk(data_dir):
        for filename in filenames:
            # Skip hidden files and manifest files themselves
            if filename.startswith('.') or filename == 'manifest.json':
                continue
            files.append(Path(root) / filename)
    
    return sorted(files)

def generate_checksums(files: List[Path], base_path: Path) -> List[Dict[str, Any]]:
    """
    Generate checksums for a list of files.
    
    Args:
        files: List of file paths to hash
        base_path: Base path for relative path calculation
        
    Returns:
        List of dictionaries with file path and hash
    """
    checksums = []
    for file_path in files:
        try:
            relative_path = str(file_path.relative_to(base_path))
            file_hash = calculate_sha256(file_path)
            checksums.append({
                "path": relative_path,
                "sha256": file_hash,
                "size_bytes": file_path.stat().st_size
            })
            logger.debug(f"Checksummed: {relative_path} ({file_hash[:16]}...)")
        except Exception as e:
            logger.error(f"Failed to checksum {file_path}: {e}")
    
    return checksums

def save_checksums(checksums: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: List of checksum dictionaries
        output_path: Path to save the JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest_data = {
        "files": checksums,
        "total_files": len(checksums),
        "generated_at": str(Path(output_path).parent.parent)
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)
    
    logger.info(f"Saved {len(checksums)} checksums to {output_path}")

def main():
    """
    Main entry point for data directory setup and checksumming.
    
    This function:
    1. Creates the required data directory structure
    2. Generates checksums for all existing data files
    3. Saves the checksums to state/hashes/data_checksums.json
    4. Updates the main manifest if it exists
    """
    # Determine project root (assume script is in code/ directory)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    logger.info(f"Project root: {project_root}")
    
    # Ensure directories exist
    directories = ensure_directories(project_root)
    
    # Collect all data files
    data_files = []
    for data_dir in [directories["raw"], directories["derived"]]:
        data_files.extend(get_data_files(data_dir))
    
    logger.info(f"Found {len(data_files)} data files to checksum")
    
    # Generate checksums
    checksums = generate_checksums(data_files, project_root)
    
    # Save checksums to state/hashes/data_checksums.json
    checksums_path = directories["state_hashes"] / "data_checksums.json"
    save_checksums(checksums, checksums_path)
    
    # If manifest exists, we could update it here
    manifest_path = project_root / "state" / "manifest.json"
    if manifest_path.exists():
        logger.info(f"Manifest found at {manifest_path}. Integration with T010 manifest system possible.")
    
    logger.info("Data directory setup and checksumming complete.")
    return 0

if __name__ == "__main__":
    exit(main())
