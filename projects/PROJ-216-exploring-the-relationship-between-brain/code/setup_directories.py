import os
import sys
from pathlib import Path
from typing import List
import datetime

def create_directories(dirs: List[str]) -> None:
    """Create all specified directories if they do not exist."""
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def verify_directories(dirs: List[str]) -> List[str]:
    """Verify that all specified directories exist."""
    missing = []
    for d in dirs:
        if not os.path.isdir(d):
            missing.append(d)
    return missing

def generate_verification_log(dirs: List[str], log_path: str = "data/.verify_structure.log") -> None:
    """Write a verification log confirming all directories were created."""
    with open(log_path, 'w') as log:
        for d in dirs:
            log.write(f'OK {d}\n')
        log.flush()

def main():
    dirs = ['data/raw', 'data/interim', 'data/processed', 'tests/unit', 'tests/integration', 'reports']
    try:
        create_directories(dirs)
        missing = verify_directories(dirs)
        if missing:
            print(f'Error: Missing directories after creation: {missing}', file=sys.stderr)
            sys.exit(1)
        
        generate_verification_log(dirs)
        print('Directories created')
        sys.exit(0)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
