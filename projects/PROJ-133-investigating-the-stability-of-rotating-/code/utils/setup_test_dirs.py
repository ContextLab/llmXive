import os
import sys
from pathlib import Path

def create_test_structure():
    """
    Create the test directory structure: tests/unit, tests/contract, tests/integration.
    Also creates __init__.py files to make them proper Python packages.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    base_path = Path("tests")
    subdirs = ["unit", "contract", "integration"]
    
    created_dirs = []
    failed_dirs = []
    
    for subdir in subdirs:
        dir_path = base_path / subdir
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
            
            # Create __init__.py to make it a package
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text(
                    "# Test package initialization\n"
                    "# This file makes the directory a Python package.\n"
                )
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
            failed_dirs.append(str(dir_path))
    
    if failed_dirs:
        print(f"Failed to create directories: {failed_dirs}", file=sys.stderr)
        return False
    
    print(f"Successfully created test directory structure:")
    for d in created_dirs:
        print(f"  - {d}")
    
    return True

def main():
    """Main entry point for the script."""
    success = create_test_structure()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
