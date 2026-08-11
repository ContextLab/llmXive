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
    directories = [
        'data/raw',
        'data/interim',
        'data/processed',
        'tests/unit',
        'tests/integration',
        'reports'
    ]
    
    created_paths = []
    for dir_path in directories:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        created_paths.append(dir_path)
    
    return created_paths

def verify_directories(paths: List[str]) -> bool:
    """
    Verifies that all specified directories exist and are writable.
    
    Args:
        paths (List[str]): List of directory paths to verify.
        
    Returns:
        bool: True if all directories exist and are writable, False otherwise.
    """
    for path_str in paths:
        path = Path(path_str)
        if not path.is_dir():
            return False
        # Check writability by attempting to create a temp file
        try:
            test_file = path / '.write_test'
            test_file.touch()
            test_file.unlink()
        except (OSError, IOError):
            return False
    return True

def generate_verification_log(paths: List[str], log_path: str = 'data/.verify_structure.log') -> None:
    """
    Generates a verification log file documenting the status of each directory.
    
    Args:
        paths (List[str]): List of directory paths to log.
        log_path (str): Path to the output log file.
    """
    log_file = Path(log_path)
    # Ensure the parent directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'w') as f:
        f.write(f"Verification Log Generated at: {datetime.datetime.now().isoformat()}\n")
        f.write("=" * 60 + "\n")
        for path_str in paths:
            path = Path(path_str)
            if path.is_dir():
                status = "OK"
            else:
                status = "FAILED"
            f.write(f"{status} {path_str}\n")

def main():
    """
    Main execution function to create, verify, and log directory structure.
    """
    print("Initializing directory structure...")
    
    # 1. Create directories
    created_paths = create_directories()
    print(f"Created directories: {created_paths}")
    
    # 2. Verify directories
    all_valid = verify_directories(created_paths)
    if not all_valid:
        print("ERROR: Directory verification failed. Some directories are missing or not writable.")
        sys.exit(1)
    print("Directory verification passed.")
    
    # 3. Generate verification log
    log_path = 'data/.verify_structure.log'
    generate_verification_log(created_paths, log_path)
    print(f"Verification log written to: {log_path}")
    
    # 4. Final check as per T001 requirements
    if not Path(log_path).exists():
        print("CRITICAL ERROR: Verification log file was not created.")
        sys.exit(1)
        
    with open(log_path, 'r') as f:
        content = f.read()
    
    # Ensure all entries are OK
    for path_str in created_paths:
        if f"OK {path_str}" not in content:
            print(f"CRITICAL ERROR: Log does not contain 'OK' status for {path_str}.")
            sys.exit(1)
            
    print("SUCCESS: All directories created, verified, and logged successfully.")

if __name__ == "__main__":
    main()
