import os
import sys
from pathlib import Path
from typing import List
import datetime

def create_directories() -> List[str]:
    """
    Create the required directory structure for the project.
    Returns a list of paths that were created or verified.
    """
    paths = [
        'data/raw',
        'data/interim',
        'data/processed',
        'tests/unit',
        'tests/integration',
        'reports'
    ]
    created_paths = []
    for p in paths:
        full_path = Path(p)
        full_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(str(full_path))
    return created_paths

def verify_directories(paths: List[str]) -> bool:
    """
    Verify that all required directories exist.
    Returns True if all exist, False otherwise.
    """
    all_exist = True
    for p in paths:
        if not Path(p).is_dir():
            all_exist = False
            print(f"ERROR: Directory {p} does not exist.")
    return all_exist

def generate_verification_log(paths: List[str], output_path: str = 'data/.verify_structure.log') -> None:
    """
    Generate a verification log file with timestamps for each directory.
    """
    timestamp = datetime.datetime.now().isoformat()
    log_entries = [f"{p}:{timestamp}" for p in paths]
    
    # Ensure the data directory exists before writing the log
    Path('data').mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(log_entries))
    
    print(f"Verification log written to {output_path}")

def main():
    """
    Main entry point to initialize the data directory structure.
    """
    print("Initializing data directory structure...")
    
    # Step 1: Create directories
    created_paths = create_directories()
    print(f"Created/Verified directories: {created_paths}")
    
    # Step 2: Verify directories
    if not verify_directories(created_paths):
        print("Verification failed. Exiting.")
        sys.exit(1)
    
    # Step 3: Generate verification log
    generate_verification_log(created_paths)
    
    print("Directory initialization complete.")

if __name__ == "__main__":
    main()
