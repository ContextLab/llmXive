"""
Checksum verification utility for data integrity.

Generates SHA256 hashes for all files in data/raw/ and stores them in data/.checksums.json.
Verifies existing files against stored hashes to detect corruption or modification.
"""
import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_config, ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CHECKSUMS_FILE = "data/.checksums.json"
DATA_RAW_DIR = "data/raw"

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string of the SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def get_all_files_in_directory(directory: Path) -> List[Path]:
    """
    Get all files in a directory recursively.
    
    Args:
        directory: Path to the directory
        
    Returns:
        List of file paths
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []
    
    files = []
    for item in directory.rglob("*"):
        if item.is_file():
            # Skip hidden files like .gitkeep if present
            if item.name.startswith('.'):
                continue
            files.append(item)
    
    return sorted(files)

def generate_checksum_manifest(files: List[Path], base_path: Path) -> Dict[str, str]:
    """
    Generate a manifest of file paths and their checksums.
    
    Args:
        files: List of file paths
        base_path: Base path to make paths relative
        
    Returns:
        Dictionary mapping relative paths to checksums
    """
    manifest = {}
    for file_path in files:
        try:
            relative_path = str(file_path.relative_to(base_path))
            checksum = compute_file_checksum(file_path)
            manifest[relative_path] = checksum
            logger.info(f"Computed checksum for {relative_path}: {checksum[:16]}...")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            continue
    
    return manifest

def save_checksums(manifest: Dict[str, str], output_path: Path) -> None:
    """
    Save checksum manifest to JSON file.
    
    Args:
        manifest: Dictionary of checksums
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "version": "1.0",
        "algorithm": "sha256",
        "generated_at": None,  # Will be set by caller if needed
        "checksums": manifest
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved checksums to {output_path}")

def load_checksums(input_path: Path) -> Dict[str, str]:
    """
    Load checksum manifest from JSON file.
    
    Args:
        input_path: Path to input JSON file
        
    Returns:
        Dictionary of checksums
    """
    if not input_path.exists():
        logger.warning(f"Checksum file not found: {input_path}")
        return {}
    
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("checksums", {})

def verify_checksums(current_manifest: Dict[str, str], stored_manifest: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Verify current files against stored checksums.
    
    Args:
        current_manifest: Current computed checksums
        stored_manifest: Stored checksums to verify against
        
    Returns:
        Tuple of (all_valid, list_of_mismatched_files)
    """
    mismatches = []
    
    # Check all stored files exist and match
    for file_path, stored_hash in stored_manifest.items():
        full_path = Path(file_path)
        if not full_path.exists():
            mismatches.append(f"MISSING: {file_path}")
            continue
        
        if file_path in current_manifest:
            if current_manifest[file_path] != stored_hash:
                mismatches.append(f"MISMATCH: {file_path}")
        else:
            # File exists but not in current manifest (shouldn't happen if we scanned same dir)
            mismatches.append(f"UNTRACKED: {file_path}")
    
    # Check for new files not in stored manifest
    for file_path in current_manifest:
        if file_path not in stored_manifest:
            mismatches.append(f"NEW_FILE: {file_path}")
    
    return len(mismatches) == 0, mismatches

def ensure_data_directories() -> None:
    """Ensure required data directories exist."""
    config = get_config()
    ensure_directories()
    
    raw_dir = Path(config["data_dir"]) / "raw"
    processed_dir = Path(config["data_dir"]) / "processed"
    validation_dir = Path(config["data_dir"]) / "validation"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    validation_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Ensured data directory structure exists")

def main() -> int:
    """
    Main entry point for checksum verification.
    
    Returns:
        0 if verification passes or generation succeeds, 1 otherwise
    """
    config = get_config()
    base_path = Path(config["project_root"])
    raw_dir = base_path / DATA_RAW_DIR
    checksums_path = base_path / CHECKSUMS_FILE
    
    # Ensure directories exist
    ensure_data_directories()
    
    # Get all files in data/raw
    files = get_all_files_in_directory(raw_dir)
    
    if not files:
        logger.warning("No files found in data/raw. Creating empty checksum manifest.")
        save_checksums({}, checksums_path)
        return 0
    
    logger.info(f"Found {len(files)} files in {DATA_RAW_DIR}")
    
    # Generate current checksums
    current_manifest = generate_checksum_manifest(files, base_path)
    
    # Load stored checksums if they exist
    stored_manifest = load_checksums(checksums_path)
    
    if stored_manifest:
        # Verify against stored
        all_valid, mismatches = verify_checksums(current_manifest, stored_manifest)
        
        if all_valid:
            logger.info("✓ All checksums match. Data integrity verified.")
            return 0
        else:
            logger.error("✗ Checksum verification failed:")
            for mismatch in mismatches:
                logger.error(f"  - {mismatch}")
            
            # If mismatches found, update the checksums file
            logger.info("Updating checksums file with current values...")
            save_checksums(current_manifest, checksums_path)
            return 1
    else:
        # No stored checksums, generate new ones
        logger.info("No existing checksums found. Generating new manifest.")
        save_checksums(current_manifest, checksums_path)
        logger.info("Checksum manifest created successfully.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
