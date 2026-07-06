"""
Data Hygiene Utilities for PROJ-329.

Provides checksumming functionality for data integrity verification
across 'data/raw/' and 'data/processed/' directories.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .state_manager import calculate_file_hash, load_state_file, save_state_file


def get_data_directories(project_root: Path) -> List[Path]:
    """
    Retrieve the list of data directories to be monitored for integrity.

    Args:
        project_root: The root path of the project.

    Returns:
        List of Path objects pointing to data/raw and data/processed.
    """
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    return [raw_dir, processed_dir]


def scan_directory_for_files(directory: Path) -> List[Path]:
    """
    Recursively scan a directory for all files.

    Args:
        directory: The directory path to scan.

    Returns:
        List of Path objects for all files found.
    """
    if not directory.exists():
        return []
    return sorted([f for f in directory.rglob("*") if f.is_file()])


def compute_checksums_for_directory(directory: Path) -> Dict[str, str]:
    """
    Compute SHA-256 checksums for all files in a directory.

    Args:
        directory: The directory to scan and hash.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    checksums = {}
    files = scan_directory_for_files(directory)
    
    for file_path in files:
        try:
            rel_path = str(file_path.relative_to(directory))
            file_hash = calculate_file_hash(file_path)
            checksums[rel_path] = file_hash
        except Exception as e:
            # Log error but continue processing other files
            print(f"Warning: Could not hash {file_path}: {e}")
    
    return checksums


def verify_data_integrity(project_root: Path, state_file: Optional[Path] = None) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Verify the integrity of data directories against stored state.

    Args:
        project_root: The root path of the project.
        state_file: Optional path to the state file (defaults to project root).

    Returns:
        Tuple of (is_valid, errors_dict).
        is_valid: True if all files match stored checksums.
        errors_dict: Dictionary mapping directory names to lists of error messages.
    """
    if state_file is None:
        state_file = project_root / "state.yaml"
    
    if not state_file.exists():
        return False, {"global": ["State file not found. Run state_manager to initialize."]}

    try:
        state = load_state_file(state_file)
    except Exception as e:
        return False, {"global": [f"Failed to load state file: {e}"]}

    data_dirs = get_data_directories(project_root)
    errors = {}
    is_valid = True

    for dir_path in data_dirs:
        dir_name = dir_path.name
        dir_errors = []

        if not dir_path.exists():
            # Directory missing is not necessarily an error if no state exists for it
            # but we log it for visibility
            continue

        current_checksums = compute_checksums_for_directory(dir_path)
        
        # Retrieve stored checksums for this directory from state
        # Assuming state structure: {'phases': [{'artifacts': {'data/raw': {...}, 'data/processed': {...}}}, ...]}
        # We look for the most recent entry containing data checksums
        stored_checksums = {}
        if "phases" in state:
            for phase in reversed(state["phases"]):
                if "artifacts" in phase:
                    if dir_name in phase["artifacts"]:
                        stored_checksums = phase["artifacts"][dir_name]
                        break
        
        # Check for missing files
        for rel_path in stored_checksums:
            if rel_path not in current_checksums:
                dir_errors.append(f"Missing file: {rel_path}")
                is_valid = False

        # Check for modified files
        for rel_path, current_hash in current_checksums.items():
            if rel_path in stored_checksums:
                if stored_checksums[rel_path] != current_hash:
                    dir_errors.append(f"Modified file: {rel_path} (hash mismatch)")
                    is_valid = False
            else:
                # New file detected
                dir_errors.append(f"New file detected (not in state): {rel_path}")
                # This might be expected during generation, so we don't flag as fatal error
                # unless strict mode is required. For now, we log it.

        if dir_errors:
            errors[dir_name] = dir_errors

    return is_valid, errors


def record_directory_state(project_root: Path, state_file: Optional[Path] = None) -> bool:
    """
    Compute current checksums for data directories and record them in state.

    Args:
        project_root: The root path of the project.
        state_file: Optional path to the state file.

    Returns:
        True if successful, False otherwise.
    """
    if state_file is None:
        state_file = project_root / "state.yaml"

    data_dirs = get_data_directories(project_root)
    artifacts = {}

    for dir_path in data_dirs:
        if dir_path.exists():
          checksums = compute_checksums_for_directory(dir_path)
          if checksums:
              artifacts[dir_path.name] = checksums

    if not artifacts:
        return True  # Nothing to record

    # Load existing state
    state = {}
    if state_file.exists():
        try:
            state = load_state_file(state_file)
        except Exception:
            state = {}

    # Append new phase state
    if "phases" not in state:
        state["phases"] = []
    
    state["phases"].append({
        "phase": "data_hygiene_scan",
        "timestamp": str(Path(project_root / "data").stat().st_mtime), # Using mtime of data dir as rough proxy
        "artifacts": artifacts
    })

    try:
        save_state_file(state_file, state)
        return True
    except Exception as e:
        print(f"Error saving state file: {e}")
        return False

def main():
    """CLI entry point for data hygiene utilities."""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Data Hygiene Utilities")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    parser.add_argument("--verify", action="store_true", help="Verify data integrity against state")
    parser.add_argument("--record", action="store_true", help="Record current data checksums to state")
    parser.add_argument("--state-file", type=Path, default=None, help="Path to state file")

    args = parser.parse_args()

    if args.verify:
        valid, errors = verify_data_integrity(args.project_root, args.state_file)
        if valid:
            print("Data integrity check passed.")
        else:
            print("Data integrity check FAILED.")
            for dir_name, errs in errors.items():
                print(f"  {dir_name}:")
                for err in errs:
                    print(f"    - {err}")
        return 0 if valid else 1

    elif args.record:
        success = record_directory_state(args.project_root, args.state_file)
        if success:
            print("Data checksums recorded successfully.")
        else:
            print("Failed to record data checksums.")
        return 0 if success else 1

    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    exit(main())
