"""
T001 Implementation: Create required project directory structure.

Creates the following directories relative to the project root:
- data/raw/
- data/processed/
- output/plots/
- code/
- code/utils/
- tests/unit/
- tests/integration/
- tests/contract/

Verification: Prints confirmation of created directories and their writability.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine project root based on script location
    # The script is in code/, so root is the parent of the code directory
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Define relative paths to create
    relative_paths = [
        "data/raw",
        "data/processed",
        "output/plots",
        "code",       # Should already exist, but ensure it's there
        "code/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]

    created_count = 0
    failed_count = 0

    print(f"Project Root: {project_root}")
    print("-" * 40)

    for rel_path in relative_paths:
        target_path = project_root / rel_path
        
        # Create directories (parents=True to create intermediate dirs if needed)
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Verify writability
            test_file = target_path / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
                writable = True
            except (OSError, PermissionError):
                writable = False

            status = "✓ Created/Writable" if writable else "✗ Not Writable"
            print(f"{rel_path}: {status}")
            
            if writable:
                created_count += 1
            else:
                failed_count += 1
                
        except Exception as e:
            print(f"{rel_path}: ✗ Error - {str(e)}")
            failed_count += 1

    print("-" * 40)
    print(f"Summary: {created_count} successful, {failed_count} failed")

    if failed_count > 0:
        print("ERROR: Some directories could not be created or verified.")
        sys.exit(1)
    else:
        print("SUCCESS: All required directories created and verified writable.")
        sys.exit(0)

if __name__ == "__main__":
    main()
