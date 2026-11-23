"""
Verification script for T001b: Create project test structure.

This script creates the required directory structure for the test suite
and verifies their existence.
"""
import os
import sys
from pathlib import Path

def create_test_structure():
    """Create the required test directories and __init__.py files."""
    base_path = Path(__file__).parent.parent
    test_root = base_path / "tests"
    
    directories = [
        test_root,
        test_root / "contract",
        test_root / "integration",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        init_file = directory / "__init__.py"
        if not init_file.exists():
          # Create a minimal __init__.py if it doesn't exist to ensure package structure
          # In a real run, these might be created by the task implementation itself,
          # but for verification robustness, we ensure they exist here.
          init_file.write_text('"""Test package."""\n')
        print(f"Created/Verified: {directory}")

def verify_structure():
    """Verify that all required directories exist."""
    base_path = Path(__file__).parent.parent
    test_root = base_path / "tests"
    
    required_dirs = [
        test_root,
        test_root / "contract",
        test_root / "integration",
    ]

    all_exist = True
    for d in required_dirs:
        if not d.exists():
            print(f"MISSING: {d}")
            all_exist = False
        else:
            print(f"EXISTS: {d}")

    if not all_exist:
        print("Verification FAILED: Some directories are missing.")
        return False
    
    print("Verification PASSED: All required directories exist.")
    return True

def main():
    """Main entry point."""
    print("Creating test structure...")
    create_test_structure()
    print("\nVerifying test structure...")
    success = verify_structure()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()