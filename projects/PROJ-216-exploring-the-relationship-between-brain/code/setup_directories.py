import os
import sys
import time
from pathlib import Path
from typing import List
import datetime

def create_directories(base_paths: List[str]) -> None:
    """Create the required directory structure."""
    for p in base_paths:
        os.makedirs(p, exist_ok=True)

def verify_directories(base_paths: List[str]) -> bool:
    """Verify that all required directories exist."""
    for p in base_paths:
        if not os.path.isdir(p):
            return False
    return True

def generate_verification_log(base_paths: List[str], log_path: str) -> None:
    """Write a verification log with timestamps for each directory."""
    entries = []
    for p in base_paths:
        # Ensure the directory exists before logging (idempotent)
        os.makedirs(p, exist_ok=True)
        timestamp = datetime.datetime.now().isoformat()
        entries.append(f"{p}:{timestamp}")
    
    # Ensure the data directory exists before writing the log file
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    with open(log_path, 'w') as f:
        f.write('\n'.join(entries))

def main() -> int:
    """Main entry point for directory initialization."""
    paths = [
        'data/raw',
        'data/interim',
        'data/processed',
        'tests/unit',
        'tests/integration',
        'reports'
    ]
    
    # Create directories
    create_directories(paths)
    
    # Verify creation
    if not verify_directories(paths):
        print("ERROR: Failed to create all required directories.", file=sys.stderr)
        return 1
    
    # Generate verification log
    log_path = 'data/.verify_structure.log'
    generate_verification_log(paths, log_path)
    
    print(f"Successfully created directories and verification log: {log_path}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
