import os
import sys
from pathlib import Path
from typing import List
import datetime

def create_directories(base_dirs: List[str]) -> bool:
    """
    Creates the required directory structure atomically.
    Returns True if all directories were created successfully, False otherwise.
    """
    for d in base_dirs:
        try:
            os.makedirs(d, exist_ok=True)
        except Exception as e:
            print(f"Error creating directory {d}: {e}", file=sys.stderr)
            return False
    return True

def verify_directories(base_dirs: List[str]) -> List[str]:
    """
    Verifies that all directories exist.
    Returns a list of directory paths that were successfully found.
    """
    found = []
    for d in base_dirs:
        if os.path.isdir(d):
            found.append(d)
    return found

def generate_verification_log(found_dirs: List[str], log_path: str = "data/.verify_structure.log") -> None:
    """
    Writes the verification log file with 'OK' prefix for each directory.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as log:
        for d in found_dirs:
            log.write(f'OK {d}\n')
        log.flush()

def main():
    """
    Main entry point for T001: Initialize Data Directory Structure.
    Creates directories, verifies them, and writes the log file.
    """
    expected_dirs = [
        'data/raw',
        'data/interim',
        'data/processed',
        'data/external',
        'tests/unit',
        'tests/integration',
        'reports'
    ]

    print("Creating directories...")
    if not create_directories(expected_dirs):
        print("Failed to create one or more directories.", file=sys.stderr)
        sys.exit(1)

    print("Verifying directories...")
    found_dirs = verify_directories(expected_dirs)
    
    if len(found_dirs) != len(expected_dirs):
        missing = set(expected_dirs) - set(found_dirs)
        print(f"Verification failed. Missing directories: {missing}", file=sys.stderr)
        sys.exit(1)

    print("Generating verification log...")
    log_path = "data/.verify_structure.log"
    generate_verification_log(found_dirs, log_path)

    print(f"Directories created and verified. Log written to {log_path}")
    sys.exit(0)

if __name__ == "__main__":
    main()
