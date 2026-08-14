"""
T001b: Create project test structure.

Creates the required directory tree for tests.
"""
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent  # 'code' directory

TEST_DIRS = [
    "tests",
    "tests/contract",
    "tests/integration",
]

def create_directories():
    """Create the directory structure if it doesn't exist."""
    created_count = 0
    for rel_path in TEST_DIRS:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")
    return created_count

def verify_structure():
    """Verify that all required directories exist."""
    print("\n--- Verifying Test Directory Structure ---")
    tests_root = PROJECT_ROOT / "tests"
    
    if not tests_root.exists():
        print(f"ERROR: Root tests directory does not exist: {tests_root}")
        return False

    required_subdirs = ["contract", "integration"]
    all_exist = True
    
    for subdir in required_subdirs:
        path = tests_root / subdir
        if path.exists() and path.is_dir():
            print(f"OK: {path}")
        else:
            print(f"MISSING: {path}")
            all_exist = False
    
    return all_exist

def main():
    """Main entry point."""
    print(f"Running T001b: Creating test structure in {PROJECT_ROOT}")
    
    created = create_directories()
    if created > 0:
        print(f"Successfully created {created} new directories.")
    
    is_valid = verify_structure()
    
    if is_valid:
        print("\n✓ Verification PASSED: All required test directories exist.")
        sys.exit(0)
    else:
        print("\n✗ Verification FAILED: Some directories are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
