"""
Test script to verify the creation of the tests/ directory structure.
This script creates the required directories and verifies their existence.
"""
import os
import sys
from pathlib import Path

def main():
    """Create and verify tests/ directory structure."""
    project_root = Path(__file__).resolve().parents[2]
    tests_root = project_root / "tests"
    
    required_dirs = [
        tests_root,
        tests_root / "contract",
        tests_root / "integration",
    ]
    
    print(f"Creating test directories under: {tests_root}")
    
    # Create directories
    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {dir_path.relative_to(project_root)}")
    
    # Verify existence
    print("\nVerifying directory structure:")
    all_exist = True
    for dir_path in required_dirs:
        exists = dir_path.exists() and dir_path.is_dir()
        status = "✓" if exists else "✗"
        print(f"  {status} {dir_path.relative_to(project_root)}")
        if not exists:
            all_exist = False
    
    if not all_exist:
        print("\nERROR: Not all required directories were created.")
        sys.exit(1)
    
    # List the structure
    print("\nDirectory listing (ls -R tests/):")
    for root, dirs, files in os.walk(tests_root):
        level = root.replace(str(tests_root), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")
    
    print("\n✓ Test directory structure verification complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
