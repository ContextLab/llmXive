import os
import sys
from pathlib import Path
from typing import List
import datetime

def create_directories(dirs: List[str]) -> None:
    """Create the required directory structure."""
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def verify_directories(dirs: List[str]) -> bool:
    """Verify that all directories exist."""
    return all(os.path.isdir(d) for d in dirs)

def generate_verification_log(dirs: List[str], log_path: str = "data/.verify_structure.log") -> None:
    """Generate a verification log file confirming directory creation."""
    with open(log_path, 'w') as log:
        for d in dirs:
            status = "OK" if os.path.isdir(d) else "FAIL"
            log.write(f"{status} {d}\n")

def main() -> None:
    """Main entry point to create and verify directories."""
    dirs = ['data/raw', 'data/interim', 'data/processed', 'tests/unit', 'tests/integration', 'reports']
    
    # Create directories
    create_directories(dirs)
    print("Directories created")
    
    # Verify and log
    generate_verification_log(dirs)
    
    # Final verification check
    if verify_directories(dirs):
        print("All directories verified successfully.")
    else:
        print("Verification failed: Some directories are missing.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
