import os
import sys
from pathlib import Path
from typing import List
import datetime

def create_directories() -> List[str]:
    """
    Creates the required directory structure for the project.
    
    Returns:
        List[str]: List of created directory paths relative to the current working directory.
    """
    dirs_to_create = [
        'data/raw',
        'data/interim',
        'data/processed',
        'tests/unit',
        'tests/integration',
        'reports'
    ]
    
    created_paths = []
    for d in dirs_to_create:
        path = Path(d)
        path.mkdir(parents=True, exist_ok=True)
        created_paths.append(d)
    
    return created_paths

def verify_directories(paths: List[str]) -> bool:
    """
    Verifies that all specified directories exist.
    
    Args:
        paths (List[str]): List of directory paths to verify.
        
    Returns:
        bool: True if all directories exist, False otherwise.
    """
    for p in paths:
        if not Path(p).is_dir():
            return False
    return True

def generate_verification_log(paths: List[str], log_path: str) -> None:
    """
    Generates a verification log file indicating the status of each directory.
    
    Args:
        paths (List[str]): List of directory paths that were attempted to be created.
        log_path (str): Path where the log file will be written.
    """
    # Ensure the log directory exists
    log_dir = Path(log_path).parent
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as log:
        log.write(f"Directory Verification Log - {datetime.datetime.now().isoformat()}\n")
        log.write("=" * 60 + "\n")
        
        for p in paths:
            status = "OK" if Path(p).is_dir() else "FAILED"
            log.write(f"{status} {p}\n")

def main():
    """
    Main entry point for the directory setup script.
    Creates directories, verifies them, and generates a log.
    """
    print("Initializing directory structure...")
    
    # 1. Create directories
    created_paths = create_directories()
    print(f"Created {len(created_paths)} directories.")
    
    # 2. Verify directories
    all_ok = verify_directories(created_paths)
    if not all_ok:
        print("ERROR: Not all directories were created successfully.")
        sys.exit(1)
    
    # 3. Generate verification log
    log_path = 'data/.verify_structure.log'
    generate_verification_log(created_paths, log_path)
    print(f"Verification log written to {log_path}")
    
    # 4. Final check for T001 requirement
    with open(log_path, 'r') as f:
        content = f.read()
    
    for p in created_paths:
        if f"OK {p}" not in content:
            print(f"CRITICAL ERROR: Verification log missing 'OK' status for {p}")
            sys.exit(1)
    
    print("Directory structure initialization complete and verified.")

if __name__ == "__main__":
    main()
