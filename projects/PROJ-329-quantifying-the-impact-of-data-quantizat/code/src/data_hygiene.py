"""
Data Hygiene Utilities for PROJ-329.

Provides checksumming, integrity verification, and state recording
for data directories (data/raw/ and data/processed/).
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from .state_manager import calculate_file_hash, load_state_file, save_state_file

logger = logging.getLogger(__name__)

# Define the project root relative to this file's location
# Assuming structure: code/src/data_hygiene.py -> project root is two levels up
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"


def get_data_directories() -> List[Path]:
    """
    Returns a list of Path objects for the primary data directories
    that require checksumming and hygiene monitoring.
    """
    dirs = []
    if DATA_RAW_DIR.exists():
        dirs.append(DATA_RAW_DIR)
    if DATA_PROCESSED_DIR.exists():
        dirs.append(DATA_PROCESSED_DIR)
    if DATA_RESULTS_DIR.exists():
        dirs.append(DATA_RESULTS_DIR)
    return dirs


def scan_directory_for_files(directory: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """
    Recursively scans a directory and returns a list of file paths.
    
    Args:
        directory: The root directory to scan.
        extensions: Optional list of file extensions to filter (e.g., ['.h5', '.json']).
                    If None, includes all files.
    
    Returns:
        List of Path objects for files found.
    """
    files = []
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return files
    
    for path in directory.rglob('*'):
        if path.is_file():
            if extensions is None or any(path.suffix == ext for ext in extensions):
                files.append(path)
    
    return sorted(files)


def compute_checksums_for_directory(directory: Path, algorithm: str = 'sha256') -> Dict[str, str]:
    """
    Computes checksums for all files in a directory recursively.
    
    Args:
        directory: The directory to scan.
        algorithm: Hash algorithm to use (default: 'sha256').
    
    Returns:
        Dictionary mapping relative file paths (string) to their checksums.
        If a file cannot be read, it is logged and skipped.
    """
    checksums = {}
    files = scan_directory_for_files(directory)
    
    for file_path in files:
        try:
            # Calculate hash relative to the directory root
            rel_path = file_path.relative_to(directory)
            file_hash = calculate_file_hash(file_path, algorithm)
            checksums[str(rel_path)] = file_hash
            logger.debug(f"Computed checksum for {rel_path}: {file_hash[:16]}...")
        except Exception as e:
            logger.error(f"Failed to compute checksum for {file_path}: {e}")
            continue
    
    return checksums


def verify_data_integrity(directory: Path, state_file: Optional[Path] = None) -> Tuple[bool, Dict[str, str], Dict[str, str]]:
    """
    Verifies the integrity of a data directory against a previously recorded state.
    
    Args:
        directory: The directory to verify.
        state_file: Optional path to the state file (yaml). If None, uses the default
                    location in the project root.
    
    Returns:
        Tuple of:
            - (bool): True if integrity is verified, False otherwise.
            - (Dict): Current checksums.
            - (Dict): Expected checksums (from state file).
    """
    if state_file is None:
        state_file = PROJECT_ROOT / "state.yaml"
    
    if not state_file.exists():
        logger.error(f"State file not found at {state_file}. Cannot verify integrity.")
        return False, {}, {}
    
    state_data = load_state_file(state_file)
    if not state_data:
        logger.error("State file is empty or invalid.")
        return False, {}, {}
    
    # Retrieve stored checksums for this directory
    dir_name = directory.name
    stored_checksums = state_data.get('data_checksums', {}).get(dir_name, {})
    
    if not stored_checksums:
        logger.warning(f"No stored checksums found for directory '{dir_name}' in state file.")
        return False, {}, stored_checksums
    
    current_checksums = compute_checksums_for_directory(directory)
    
    # Compare
    is_valid = True
    if set(current_checksums.keys()) != set(stored_checksums.keys()):
        logger.warning(f"File mismatch in {dir_name}. Expected {len(stored_checksums)}, found {len(current_checksums)}.")
        is_valid = False
    
    for rel_path, current_hash in current_checksums.items():
        if rel_path not in stored_checksums:
            logger.warning(f"New file detected: {rel_path}")
            is_valid = False
        elif stored_checksums[rel_path] != current_hash:
            logger.warning(f"Checksum mismatch for {rel_path}: expected {stored_checksums[rel_path][:16]}..., got {current_hash[:16]}...")
            is_valid = False
    
    return is_valid, current_checksums, stored_checksums


def record_directory_state(directory: Path, state_file: Optional[Path] = None, phase: str = "hygiene") -> bool:
    """
    Computes checksums for a directory and records them in the state file.
    
    Args:
        directory: The directory to scan and record.
        state_file: Optional path to the state file.
        phase: The phase name to record in the state (e.g., "T005_hygiene").
    
    Returns:
        True if successful, False otherwise.
    """
    if not directory.exists():
        logger.error(f"Directory does not exist: {directory}")
        return False
    
    checksums = compute_checksums_for_directory(directory)
    
    if state_file is None:
        state_file = PROJECT_ROOT / "state.yaml"
    
    state_data = load_state_file(state_file)
    if state_data is None:
        state_data = {'phases': {}, 'data_checksums': {}}
    
    if 'data_checksums' not in state_data:
        state_data['data_checksums'] = {}
    
    state_data['data_checksums'][directory.name] = checksums
    
    # Record phase metadata
    phase_key = f"{phase}_{directory.name}"
    state_data['phases'][phase_key] = {
        'timestamp': str(Path(directory).stat().st_mtime),
        'file_count': len(checksums),
        'checksum_sample': list(checksums.values())[:3] if checksums else []
    }
    
    return save_state_file(state_file, state_data)


def main():
    """
    CLI entry point for data hygiene verification and recording.
    Usage: python -m src.data_hygiene [command] [directory_name]
    Commands:
      verify  : Verify integrity against state.yaml
      record  : Record current state to state.yaml
      scan    : Just list files and checksums
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Hygiene Utilities")
    parser.add_argument('command', choices=['verify', 'record', 'scan'], help="Operation to perform")
    parser.add_argument('directory', nargs='?', default=None, help="Directory name (raw, processed, results) or 'all'")
    
    args = parser.parse_args()
    
    dirs_to_process = []
    
    if args.directory:
        if args.directory == 'all':
            dirs_to_process = get_data_directories()
        else:
            target = PROJECT_ROOT / "data" / args.directory
            if target.exists():
                dirs_to_process.append(target)
            else:
                logger.error(f"Directory not found: {target}")
                return
    else:
        dirs_to_process = get_data_directories()
    
    if not dirs_to_process:
        logger.info("No data directories found.")
        return
    
    for directory in dirs_to_process:
        logger.info(f"Processing directory: {directory}")
        if args.command == 'verify':
            is_valid, current, expected = verify_data_integrity(directory)
            status = "PASS" if is_valid else "FAIL"
            logger.info(f"Integrity check for {directory.name}: {status}")
            if not is_valid:
                logger.warning("Differences found. Run 'record' to update state.")
        elif args.command == 'record':
            success = record_directory_state(directory)
            if success:
                logger.info(f"State recorded for {directory.name}")
            else:
                logger.error(f"Failed to record state for {directory.name}")
        elif args.command == 'scan':
            checksums = compute_checksums_for_directory(directory)
            logger.info(f"Found {len(checksums)} files in {directory.name}")
            for rel_path, checksum in checksums.items():
                logger.info(f"  {rel_path}: {checksum[:16]}...")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
