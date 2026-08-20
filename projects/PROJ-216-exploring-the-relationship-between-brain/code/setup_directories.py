import os
import sys
from pathlib import Path
from typing import List
import datetime

def create_directories() -> List[str]:
    """
    Creates the required project directories:
    data/raw, data/interim, data/processed,
    tests/unit, tests/integration, reports
    
    Returns a list of created directory paths.
    """
    base = Path(".")
    dirs = [
        base / "data" / "raw",
        base / "data" / "interim",
        base / "data" / "processed",
        base / "tests" / "unit",
        base / "tests" / "integration",
        base / "reports"
    ]
    
    created = []
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        created.append(str(d))
    
    return created

def verify_directories(paths: List[str]) -> List[str]:
    """
    Verifies that all given paths exist and are directories.
    Returns a list of paths that are valid directories.
    """
    valid = []
    for p in paths:
        if os.path.isdir(p):
            valid.append(p)
    return valid

def generate_verification_log(valid_paths: List[str], log_path: str = "data/.verify_structure.log") -> None:
    """
    Writes a verification log file indicating successful creation of directories.
    Format: OK <path>
    """
    timestamp = datetime.datetime.now().isoformat()
    with open(log_path, 'w') as f:
        f.write(f"# Verification Log generated at {timestamp}\n")
        for p in valid_paths:
            f.write(f"OK {p}\n")
        f.flush()

def main():
    """
    Main entry point: creates directories, verifies them, and writes the log.
    Exits with 0 on success, 1 on failure.
    """
    try:
        # Create directories
        created_dirs = create_directories()
        
        # Verify they exist
        valid_dirs = verify_directories(created_dirs)
        
        if len(valid_dirs) != len(created_dirs):
            missing = set(created_dirs) - set(valid_dirs)
            print(f"Error: Failed to create/verify directories: {missing}", file=sys.stderr)
            sys.exit(1)
        
        # Write verification log
        log_path = "data/.verify_structure.log"
        generate_verification_log(valid_dirs, log_path)
        
        print("Directories created")
        sys.exit(0)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
