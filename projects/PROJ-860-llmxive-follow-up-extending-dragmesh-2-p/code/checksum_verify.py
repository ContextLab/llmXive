"""
Checksum verification utility for DragMesh-2 project data integrity.

This module provides functions to compute SHA256 hashes for files in data directories,
verify data integrity, and update the project state file with current checksums.

Satisfies Constitution Principle III (Data Hygiene) and FR-007 (clamping/stiction safety).
"""
import os
import sys
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_GENERATED_DIR = PROJECT_ROOT / "data" / "generated"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml"

def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string representation of the SHA256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except PermissionError as e:
        logger.error(f"Permission denied reading file: {file_path}")
        raise

def scan_directory(directory: Path) -> List[Path]:
    """
    Recursively scan a directory for all files.
    
    Args:
        directory: Path to the directory to scan.
        
    Returns:
        List of Path objects for all files found.
        
    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []
    
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            # Skip hidden files and checksum files themselves
            if filename.startswith('.') or filename == '.checksums':
                continue
            files.append(Path(root) / filename)
    return files

def load_existing_checksums() -> Dict:
    """
    Load existing checksums from the state file.
    
    Returns:
        Dictionary containing the state data, or empty dict if file doesn't exist.
    """
    if not STATE_FILE.exists():
        logger.info(f"State file not found, creating new: {STATE_FILE}")
        return {}
    
    try:
        with open(STATE_FILE, 'r') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing state file: {e}")
        return {}

def save_checksums(state_data: Dict) -> None:
    """
    Save updated checksums to the state file.
    
    Args:
        state_data: Dictionary containing the updated state data.
    """
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Updated state file: {STATE_FILE}")

def verify_data_integrity(checksums: Dict[str, str], directory: Path) -> Tuple[bool, List[str]]:
    """
    Verify files against stored checksums.
    
    Args:
        checksums: Dictionary mapping relative file paths to expected hashes.
        directory: Base directory for the files.
        
    Returns:
        Tuple of (all_valid, list_of_failed_files).
    """
    all_valid = True
    failed_files = []
    
    for rel_path, expected_hash in checksums.items():
        file_path = directory / rel_path
        if not file_path.exists():
            logger.warning(f"File missing during verification: {file_path}")
            all_valid = False
            failed_files.append(rel_path)
            continue
        
        try:
            actual_hash = compute_sha256(file_path)
            if actual_hash != expected_hash:
                logger.warning(f"Checksum mismatch for {file_path}: expected {expected_hash}, got {actual_hash}")
                all_valid = False
                failed_files.append(rel_path)
            else:
                logger.debug(f"Verified: {file_path}")
        except Exception as e:
            logger.error(f"Error verifying {file_path}: {e}")
            all_valid = False
            failed_files.append(rel_path)
    
    return all_valid, failed_files

def update_checksums(directory: Path, state_key: str, state_data: Dict) -> Dict[str, str]:
    """
    Compute checksums for all files in a directory and update state.
    
    Args:
        directory: Directory to scan for files.
        state_key: Key in state_data where checksums should be stored.
        state_data: The state dictionary to update.
        
    Returns:
        Dictionary of new checksums.
    """
    files = scan_directory(directory)
    new_checksums = {}
    
    if not files:
        logger.info(f"No files found in {directory}")
        state_data.setdefault("artifact_hashes", {})[state_key] = {}
        return new_checksums
    
    logger.info(f"Computing checksums for {len(files)} files in {directory}...")
    
    for file_path in files:
        try:
            rel_path = str(file_path.relative_to(directory))
            file_hash = compute_sha256(file_path)
            new_checksums[rel_path] = file_hash
            logger.debug(f"Hashed: {rel_path} -> {file_hash[:16]}...")
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
    
    # Update state
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    state_data["artifact_hashes"][state_key] = new_checksums
    
    return new_checksums

def main():
    """
    Main entry point for checksum verification and state update.
    
    This function:
    1. Scans data/raw and data/generated directories.
    2. Computes SHA256 hashes for all files.
    3. Verifies against existing checksums if available.
    4. Updates the project state file with new checksums.
    """
    logger.info("Starting checksum verification and state update...")
    
    # Load existing state
    state_data = load_existing_checksums()
    
    # Process data/raw
    if DATA_RAW_DIR.exists():
        logger.info(f"Processing {DATA_RAW_DIR}...")
        raw_checksums = update_checksums(DATA_RAW_DIR, "data_raw", state_data)
        if raw_checksums:
            logger.info(f"Computed {len(raw_checksums)} checksums for data/raw")
    else:
        logger.warning(f"Directory not found: {DATA_RAW_DIR}")
        state_data.setdefault("artifact_hashes", {})["data_raw"] = {}
    
    # Process data/generated
    if DATA_GENERATED_DIR.exists():
        logger.info(f"Processing {DATA_GENERATED_DIR}...")
        generated_checksums = update_checksums(DATA_GENERATED_DIR, "data_generated", state_data)
        if generated_checksums:
            logger.info(f"Computed {len(generated_checksums)} checksums for data/generated")
    else:
        logger.warning(f"Directory not found: {DATA_GENERATED_DIR}")
        state_data.setdefault("artifact_hashes", {})["data_generated"] = {}
    
    # Verify existing checksums (if any)
    if "artifact_hashes" in state_data:
        if "data_raw" in state_data["artifact_hashes"]:
            valid, failed = verify_data_integrity(state_data["artifact_hashes"]["data_raw"], DATA_RAW_DIR)
            if not valid:
                logger.warning(f"Verification failed for {len(failed)} files in data/raw")
        
        if "data_generated" in state_data["artifact_hashes"]:
            valid, failed = verify_data_integrity(state_data["artifact_hashes"]["data_generated"], DATA_GENERATED_DIR)
            if not valid:
                logger.warning(f"Verification failed for {len(failed)} files in data/generated")
    
    # Save updated state
    save_checksums(state_data)
    
    logger.info("Checksum verification and state update completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())