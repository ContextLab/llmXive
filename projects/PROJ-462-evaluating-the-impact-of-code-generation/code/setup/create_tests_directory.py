"""Create the tests directory structure for the project.

This script creates the following directory structure:
- tests/
- tests/unit/
- tests/integration/
- tests/contract/

Each directory includes an __init__.py file to make them proper Python packages.
"""
import os
import sys
from pathlib import Path


def create_tests_directory(root_path: Path = None) -> dict:
    """Create the tests directory structure.
    
    Args:
        root_path: The project root path. Defaults to current working directory.
        
    Returns:
        dict with status information about created directories
    """
    if root_path is None:
        root_path = Path.cwd()
    
    tests_base = root_path / "tests"
    subdirectories = ["unit", "integration", "contract"]
    
    created_dirs = []
    created_files = []
    errors = []
    
    # Create base tests directory
    try:
        tests_base.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(tests_base))
        
        # Create __init__.py for tests package
        init_file = tests_base / "__init__.py"
        init_file.write_text(
            "# Tests package for PROJ-462-evaluating-the-impact-of-code-generation\n"
            "# This package contains unit, integration, and contract tests.\n"
        )
        created_files.append(str(init_file))
        
    except Exception as e:
        errors.append(f"Failed to create {tests_base}: {e}")
    
    # Create subdirectories
    for subdir in subdirectories:
        subdir_path = tests_base / subdir
        try:
            subdir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(subdir_path))
            
            # Create __init__.py for each subpackage
            init_file = subdir_path / "__init__.py"
            init_file.write_text(
                f"# {subdir.capitalize()} tests package\n"
                f"# Contains {subdir} tests for PROJ-462-evaluating-the-impact-of-code-generation\n"
            )
            created_files.append(str(init_file))
            
        except Exception as e:
            errors.append(f"Failed to create {subdir_path}: {e}")
    
    return {
        "status": "success" if not errors else "partial",
        "created_directories": created_dirs,
        "created_files": created_files,
        "errors": errors,
        "total_directories_created": len(created_dirs),
        "total_files_created": len(created_files)
    }


def main():
    """Entry point for command-line execution."""
    root_path = Path.cwd()
    
    print(f"Creating tests directory structure at: {root_path}")
    
    result = create_tests_directory(root_path)
    
    print(f"\nStatus: {result['status'].upper()}")
    print(f"Directories created: {result['total_directories_created']}")
    print(f"Files created: {result['total_files_created']}")
    
    if result['created_directories']:
        print("\nDirectories:")
        for d in result['created_directories']:
            print(f"  - {d}")
    
    if result['created_files']:
        print("\nFiles:")
        for f in result['created_files']:
            print(f"  - {f}")
    
    if result['errors']:
        print("\nErrors:")
        for e in result['errors']:
            print(f"  - {e}")
        sys.exit(1)
    
    print("\nTests directory structure created successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
