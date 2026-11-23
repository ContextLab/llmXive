"""
Setup script to create the tests directory structure.

This script creates the necessary directory hierarchy for unit and integration tests
as specified in task T001c.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Ensure we are running from the project root or code directory
# The script assumes it is located in the 'code' directory relative to the project root
# or that the project root is the parent of this file's directory.
# For this project structure, we assume the script is run from the project root
# or that `code/` is the immediate parent.

def create_tests_directories(base_dir: Path):
    """
    Create the tests directory structure.
    
    Args:
        base_dir: The root directory of the project.
    """
    tests_root = base_dir / "tests"
    unit_dir = tests_root / "unit"
    integration_dir = tests_root / "integration"
    
    directories = [tests_root, unit_dir, integration_dir]
    
    created = []
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory.relative_to(base_dir)))
            # Create __init__.py to make them proper Python packages
            init_file = directory / "__init__.py"
            if not init_file.exists():
                init_file.touch()
        else:
            # Ensure __init__.py exists if directory already existed
            init_file = directory / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                
    return created

def main():
    """Main entry point for the setup script."""
    # Determine project root: assume this file is in code/, so parent is root
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    project_root = code_dir.parent
    
    print(f"[{datetime.now().isoformat()}] Creating tests directory structure at: {project_root}")
    
    try:
        created_dirs = create_tests_directories(project_root)
        if created_dirs:
            print(f"Created directories: {', '.join(created_dirs)}")
        else:
            print("All directories already exist.")
            
        # Verification output
        print(f"\nVerification (ls -R tests/):")
        tests_root = project_root / "tests"
        for root, dirs, files in os.walk(tests_root):
            level = root.replace(str(tests_root), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f'{subindent}{file}')
                
        print("\n[T001c] Task completed successfully.")
        return 0
        
    except Exception as e:
        print(f"[ERROR] Failed to create tests directory structure: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
