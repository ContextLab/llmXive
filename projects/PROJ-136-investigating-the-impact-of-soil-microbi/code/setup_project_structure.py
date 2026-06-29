"""
T001: Create project structure per implementation plan.

Creates the following directories:
- data/raw/
- data/processed/
- code/analysis/
- code/tests/
- code/tests/contract/
- code/tests/integration/
- code/tests/unit/
- state/
"""

import os
import sys
from pathlib import Path

def create_directories():
    """Create all required project directories."""
    # Define the project root (current directory)
    root = Path.cwd()
    
    # Define relative paths as per task specification
    directories = [
        "data/raw",
        "data/processed",
        "code/analysis",
        "code/tests",
        "code/tests/contract",
        "code/tests/integration",
        "code/tests/unit",
        "state"
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = root / dir_path
        try:
            if full_path.exists():
                print(f"SKIP: Directory already exists: {full_path}")
                skipped_count += 1
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"CREATE: {full_path}")
                created_count += 1
        except OSError as e:
            print(f"ERROR: Failed to create {full_path}: {e}")
            return False
    
    print(f"\nSummary: {created_count} created, {skipped_count} skipped")
    return True

def verify_structure():
    """Verify all required directories exist."""
    root = Path.cwd()
    directories = [
        "data/raw",
        "data/processed",
        "code/analysis",
        "code/tests",
        "code/tests/contract",
        "code/tests/integration",
        "code/tests/unit",
        "state"
    ]
    
    missing = []
    for dir_path in directories:
        if not (root / dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        print(f"VERIFICATION FAILED: Missing directories: {missing}")
        return False
    
    print("VERIFICATION PASSED: All required directories exist.")
    return True

if __name__ == "__main__":
    print("=== T001: Creating Project Structure ===")
    success = create_directories()
    if success:
        success = verify_structure()
    
    sys.exit(0 if success else 1)
