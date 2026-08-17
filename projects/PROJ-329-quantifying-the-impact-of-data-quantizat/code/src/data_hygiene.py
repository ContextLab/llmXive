"""
Data hygiene utilities for checksumming and integrity verification.

Provides functions to:
- Scan directories for data files
- Compute checksums (SHA-256) for files and directories
- Verify data integrity against stored state
- Record directory state to state.yaml
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from .state_manager import calculate_file_hash, load_state_file, save_state_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_data_directories() -> Dict[str, Path]:
    """
    Returns a dictionary of standard data directories relative to the project root.
    
    Returns:
        Dict mapping directory names ('raw', 'processed', 'results') to their Path objects.
    """
    # Determine project root (parent of 'code')
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    data_root = project_root / "data"
    
    return {
        "raw": data_root / "raw",
        "processed": data_root / "processed",
        "results": data_root / "results"
    }

def scan_directory_for_files(directory: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """
    Recursively scan a directory for files with specified extensions.
    
    Args:
        directory: Path to the directory to scan.
        extensions: Optional list of file extensions to include (e.g., ['.h5', '.csv']).
                   If None, includes all files.
    
    Returns:
        List of Path objects for matching files.
    
    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")
    
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = Path(root) / filename
            if extensions is None or any(filename.endswith(ext) for ext in extensions):
                files.append(file_path)
    
    return sorted(files)

def compute_checksums_for_directory(directory: Path, extensions: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Compute SHA-256 checksums for all files in a directory.
    
    Args:
        directory: Path to the directory to scan.
        extensions: Optional list of file extensions to include.
    
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hex digest.
    
    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    checksums = {}
    files = scan_directory_for_files(directory, extensions)
    
    for file_path in files:
        relative_path = str(file_path.relative_to(directory))
        checksums[relative_path] = calculate_file_hash(file_path)
        logger.debug(f"Computed checksum for {relative_path}: {checksums[relative_path][:16]}...")
    
    return checksums

def verify_data_integrity(directory: Path, state_file: Optional[Path] = None) -> Tuple[bool, Dict[str, str]]:
    """
    Verify the integrity of a directory against a stored state.
    
    Args:
        directory: Path to the directory to verify.
        state_file: Optional path to the state.yaml file. If None, looks for state.yaml
                   in the project root.
    
    Returns:
        Tuple of (is_valid, details_dict).
        - is_valid: True if all files match their stored checksums.
        - details_dict: Contains 'missing', 'modified', and 'unchanged' lists.
    """
    project_root = directory.parent.parent
    if state_file is None:
        state_file = project_root / "state.yaml"
    
    if not state_file.exists():
        logger.warning(f"State file not found: {state_file}. Cannot verify integrity.")
        return False, {"error": "State file not found"}
    
    state = load_state_file(state_file)
    
    # Find the directory entry in state
    dir_name = directory.name
    dir_key = None
    for key in state.get("data_checksums", {}).keys():
        if key.endswith(dir_name):
            dir_key = key
            break
    
    if dir_key is None:
        logger.warning(f"No stored state for directory: {directory}")
        return False, {"error": "No stored state for directory"}
    
    stored_checksums = state["data_checksums"][dir_key]
    current_checksums = compute_checksums_for_directory(directory)
    
    missing = []
    modified = []
    unchanged = []
    
    # Check for missing files
    for rel_path in stored_checksums:
        if rel_path not in current_checksums:
            missing.append(rel_path)
    
    # Check for modified or new files
    for rel_path, current_hash in current_checksums.items():
        if rel_path not in stored_checksums:
            modified.append(f"{rel_path} (new file)")
        elif stored_checksums[rel_path] != current_hash:
            modified.append(rel_path)
        else:
            unchanged.append(rel_path)
    
    is_valid = len(missing) == 0 and len(modified) == 0
    
    details = {
        "missing": missing,
        "modified": modified,
        "unchanged": unchanged,
        "total_stored": len(stored_checksums),
        "total_current": len(current_checksums)
    }
    
    if is_valid:
        logger.info(f"Integrity check PASSED for {directory}")
    else:
        logger.warning(f"Integrity check FAILED for {directory}: {len(missing)} missing, {len(modified)} modified")
    
    return is_valid, details

def record_directory_state(directory: Path, state_file: Optional[Path] = None) -> Dict[str, str]:
    """
    Compute and record the current state (checksums) of a directory.
    
    Args:
        directory: Path to the directory to record.
        state_file: Optional path to the state.yaml file. If None, uses project root.
    
    Returns:
        The computed checksums dictionary.
    """
    project_root = directory.parent.parent
    if state_file is None:
        state_file = project_root / "state.yaml"
    
    checksums = compute_checksums_for_directory(directory)
    
    # Load existing state or create new
    if state_file.exists():
        state = load_state_file(state_file)
    else:
        state = {"data_checksums": {}}
    
    if "data_checksums" not in state:
        state["data_checksums"] = {}
    
    # Use directory name as key
    dir_key = directory.name
    state["data_checksums"][dir_key] = checksums
    
    save_state_file(state, state_file)
    logger.info(f"Recorded state for {directory} ({len(checksums)} files) to {state_file}")
    
    return checksums

def main():
    """
    CLI entry point for data hygiene operations.
    
    Usage:
        python -m src.data_hygiene check <directory>
        python -m src.data_hygiene record <directory>
        python -m src.data_hygiene scan <directory> [--ext .h5,.csv]
    """
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python -m src.data_hygiene <command> <directory> [options]")
        print("Commands: check, record, scan")
        sys.exit(1)
    
    command = sys.argv[1]
    directory_path = Path(sys.argv[2])
    
    if not directory_path.exists():
        print(f"Error: Directory not found: {directory_path}")
        sys.exit(1)
    
    if command == "check":
        is_valid, details = verify_data_integrity(directory_path)
        print(f"Directory: {directory_path}")
        print(f"Integrity: {'PASSED' if is_valid else 'FAILED'}")
        if not is_valid:
            if "missing" in details:
                print(f"  Missing: {len(details.get('missing', []))} files")
            if "modified" in details:
                print(f"  Modified: {len(details.get('modified', []))} files")
    elif command == "record":
        checksums = record_directory_state(directory_path)
        print(f"Recorded {len(checksums)} files for {directory_path}")
    elif command == "scan":
        extensions = None
        if "--ext" in sys.argv:
            idx = sys.argv.index("--ext")
            if idx + 1 < len(sys.argv):
                extensions = sys.argv[idx + 1].split(",")
        
        files = scan_directory_for_files(directory_path, extensions)
        print(f"Found {len(files)} files in {directory_path}")
        for f in files:
            print(f"  {f}")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
