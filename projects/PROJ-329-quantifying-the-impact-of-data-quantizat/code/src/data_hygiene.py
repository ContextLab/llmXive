"""
Data Hygiene Utilities for PROJ-329.

Provides functions to compute checksums (SHA-256) for files in the
data/raw/ and data/processed/ directories, verify data integrity
against a stored state, and record directory state snapshots.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from .state_manager import calculate_file_hash, load_state_file, save_state_file

logger = logging.getLogger(__name__)


def get_data_directories(project_root: Optional[Path] = None) -> Tuple[Path, Path]:
    """
    Returns the absolute paths for the data/raw and data/processed directories.
    
    Args:
        project_root: Optional root path. Defaults to parent of this module's directory.
        
    Returns:
        Tuple of (raw_dir, processed_dir) as Path objects.
    """
    if project_root is None:
        # Default to the project root relative to this file's location
        # Assuming structure: code/src/data_hygiene.py -> project root is 2 levels up
        project_root = Path(__file__).resolve().parent.parent.parent
    
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    
    # Ensure directories exist (create if missing to avoid errors during scan)
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    return raw_dir, processed_dir


def scan_directory_for_files(directory: Path) -> List[Path]:
    """
    Recursively scans a directory and returns a list of all regular files.
    
    Args:
        directory: Path to the directory to scan.
        
    Returns:
        List of Path objects for all regular files found.
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []
    
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            # Skip hidden files and temporary editor files
            if filename.startswith('.') or filename.endswith('~'):
                continue
            files.append(Path(root) / filename)
    
    return sorted(files)


def compute_checksums_for_directory(directory: Path) -> Dict[str, str]:
    """
    Computes SHA-256 checksums for all files in a directory.
    
    Args:
        directory: Path to the directory to checksum.
        
    Returns:
        Dictionary mapping relative file paths (string) to their SHA-256 hex digest.
    """
    checksums = {}
    files = scan_directory_for_files(directory)
    
    for file_path in files:
        try:
            # Use the state_manager's hash function which handles binary reading
            file_hash = calculate_file_hash(file_path)
            rel_path = str(file_path.relative_to(directory))
            checksums[rel_path] = file_hash
            logger.debug(f"Computed checksum for {rel_path}: {file_hash[:16]}...")
        except Exception as e:
            logger.error(f"Failed to compute checksum for {file_path}: {e}")
            # Continue processing other files, but log the error
            continue
    
    return checksums


def verify_data_integrity(
    raw_checksums: Dict[str, str],
    processed_checksums: Dict[str, str],
    state_file_path: Optional[Path] = None
) -> Tuple[bool, List[str]]:
    """
    Verifies current data checksums against a previously recorded state.
    
    Args:
        raw_checksums: Current checksums for data/raw/
        processed_checksums: Current checksums for data/processed/
        state_file_path: Path to the state.yaml file. Defaults to project root.
        
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    is_valid = True
    
    if state_file_path is None:
        state_file_path = Path(__file__).resolve().parent.parent.parent / "state.yaml"
    
    if not state_file_path.exists():
        errors.append(f"State file not found at {state_file_path}. No previous state to verify against.")
        return False, errors
    
    try:
        state_data = load_state_file(state_file_path)
    except Exception as e:
        errors.append(f"Failed to load state file: {e}")
        return False, errors
    
    # Check raw directory state
    if "data_raw" in state_data:
        stored_raw = state_data["data_raw"]
        if set(raw_checksums.keys()) != set(stored_raw.keys()):
            # Check if files were added or removed
            current_files = set(raw_checksums.keys())
            stored_files = set(stored_raw.keys())
            
            added = current_files - stored_files
            removed = stored_files - current_files
            
            if added:
                errors.append(f"New files detected in data/raw/: {added}")
            if removed:
                errors.append(f"Files missing in data/raw/: {removed}")
            is_valid = False
        
        # Check content integrity for existing files
        for rel_path, current_hash in raw_checksums.items():
            if rel_path in stored_raw:
                if current_hash != stored_raw[rel_path]:
                    errors.append(f"Integrity check failed for data/raw/{rel_path}: hash mismatch.")
                    is_valid = False
    else:
        # If state exists but no data_raw key, it might be the first run or a different schema
        logger.warning("No 'data_raw' state found in state file. Assuming first run or schema mismatch.")
    
    # Check processed directory state
    if "data_processed" in state_data:
        stored_processed = state_data["data_processed"]
        if set(processed_checksums.keys()) != set(stored_processed.keys()):
            current_files = set(processed_checksums.keys())
            stored_files = set(stored_processed.keys())
            
            added = current_files - stored_files
            removed = stored_files - current_files
            
            if added:
                errors.append(f"New files detected in data/processed/: {added}")
            if removed:
                errors.append(f"Files missing in data/processed/: {removed}")
            is_valid = False
        
        for rel_path, current_hash in processed_checksums.items():
            if rel_path in stored_processed:
                if current_hash != stored_processed[rel_path]:
                    errors.append(f"Integrity check failed for data/processed/{rel_path}: hash mismatch.")
                    is_valid = False
    else:
        logger.warning("No 'data_processed' state found in state file.")
    
    return is_valid, errors


def record_directory_state(
    raw_checksums: Dict[str, str],
    processed_checksums: Dict[str, str],
    state_file_path: Optional[Path] = None
) -> bool:
    """
    Records the current checksum state to the state file.
    
    Args:
        raw_checksums: Current checksums for data/raw/
        processed_checksums: Current checksums for data/processed/
        state_file_path: Path to the state.yaml file.
        
    Returns:
        True if successful, False otherwise.
    """
    if state_file_path is None:
        state_file_path = Path(__file__).resolve().parent.parent.parent / "state.yaml"
    
    try:
        # Load existing state or create new
        state_data = load_state_file(state_file_path) if state_file_path.exists() else {}
        
        # Update with new checksums
        state_data["data_raw"] = raw_checksums
        state_data["data_processed"] = processed_checksums
        
        # Save back to file
        save_state_file(state_data, state_file_path)
        logger.info(f"Directory state recorded to {state_file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to record directory state: {e}")
        return False


def main():
    """
    CLI entry point for running data hygiene checks.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Hygiene: Checksum and Verify")
    parser.add_argument("--action", choices=["compute", "verify", "record"], default="compute",
                      help="Action to perform: compute (scan and print), verify (check against state), record (save state)")
    parser.add_argument("--project-root", type=str, default=None, help="Project root directory")
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root) if args.project_root else None
    raw_dir, processed_dir = get_data_directories(project_root)
    
    logger.info(f"Scanning {raw_dir} and {processed_dir}...")
    
    raw_checksums = compute_checksums_for_directory(raw_dir)
    processed_checksums = compute_checksums_for_directory(processed_dir)
    
    if args.action == "compute":
        print(f"Raw files ({len(raw_checksums)}):")
        for path, hash_val in raw_checksums.items():
            print(f"  {path}: {hash_val[:16]}...")
        print(f"Processed files ({len(processed_checksums)}):")
        for path, hash_val in processed_checksums.items():
            print(f"  {path}: {hash_val[:16]}...")
            
    elif args.action == "verify":
        is_valid, errors = verify_data_integrity(raw_checksums, processed_checksums)
        if is_valid:
            print("✓ Data integrity verified successfully.")
        else:
            print("✗ Data integrity check FAILED.")
            for err in errors:
                print(f"  - {err}")
                
    elif args.action == "record":
        success = record_directory_state(raw_checksums, processed_checksums)
        if success:
            print("✓ Directory state recorded successfully.")
        else:
            print("✗ Failed to record directory state.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
