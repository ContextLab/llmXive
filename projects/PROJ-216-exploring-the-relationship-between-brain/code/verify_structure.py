"""
Standalone script to execute T001 verification logic as described in tasks.md.
This script creates the directories, verifies them, and writes the log.
It exits with code 1 if verification fails.
"""
import os
import sys
from pathlib import Path

def main():
    dirs = ['data/raw', 'data/interim', 'data/processed', 'tests/unit', 'tests/integration', 'reports']
    
    # Create directories
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    print("Directories created")
    
    # Write verification log
    log_path = 'data/.verify_structure.log'
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'w') as log:
        for d in dirs:
            if Path(d).is_dir():
                log.write(f'OK {d}\n')
            else:
                log.write(f'FAILED {d}\n')
                print(f"ERROR: Directory {d} was not created.")
                sys.exit(1)
    
    # Verification check
    with open(log_file, 'r') as f:
        content = f.read()
    
    all_ok = True
    for d in dirs:
        if f'OK {d}' not in content:
            all_ok = False
            print(f"ERROR: Log missing 'OK' for {d}")
    
    if not all_ok:
        print("VERIFICATION FAILED: Log does not contain 'OK' for all directories.")
        sys.exit(1)
    
    print("VERIFICATION PASSED: All directories exist and logged as OK.")

if __name__ == "__main__":
    main()