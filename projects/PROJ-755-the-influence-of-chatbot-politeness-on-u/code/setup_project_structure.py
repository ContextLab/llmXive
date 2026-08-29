"""
Script to create the project directory structure for the llmXive science pipeline.
This script creates the required directories and .gitkeep files to ensure
the directory structure is preserved in version control.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

def create_structure(base_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Create the project directory structure.

    Args:
        base_path: The base directory for the project. Defaults to current working directory.

    Returns:
        A dictionary containing:
            - created_directories: List of created directory paths
            - created_files: List of created .gitkeep file paths
            - errors: List of any errors encountered
    """
    if base_path is None:
        base_path = Path.cwd()

    # Define the required directory structure
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs",
        "state",
        "contracts",
        "figures",
    ]

    created_directories = []
    created_files = []
    errors = []

    # Create directories
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_directories.append(str(full_path))
            print(f"Created directory: {full_path}")
        except Exception as e:
            error_msg = f"Failed to create directory {full_path}: {str(e)}"
            errors.append(error_msg)
            print(error_msg, file=sys.stderr)

    # Create .gitkeep files in data directories to ensure they are tracked by git
    data_dirs = ["data/raw", "data/processed"]
    for dir_path in data_dirs:
        full_path = base_path / dir_path / ".gitkeep"
        try:
            full_path.touch()
            created_files.append(str(full_path))
            print(f"Created .gitkeep file: {full_path}")
        except Exception as e:
            error_msg = f"Failed to create .gitkeep file {full_path}: {str(e)}"
            errors.append(error_msg)
            print(error_msg, file=sys.stderr)

    # Create .gitkeep files in tests directories
    test_dirs = ["tests/contract", "tests/unit", "tests/integration"]
    for dir_path in test_dirs:
        full_path = base_path / dir_path / ".gitkeep"
        try:
            full_path.touch()
            created_files.append(str(full_path))
            print(f"Created .gitkeep file: {full_path}")
        except Exception as e:
            error_msg = f"Failed to create .gitkeep file {full_path}: {str(e)}"
            errors.append(error_msg)
            print(error_msg, file=sys.stderr)

    # Create .gitkeep file in state directory
    state_path = base_path / "state" / ".gitkeep"
    try:
        state_path.touch()
        created_files.append(str(state_path))
        print(f"Created .gitkeep file: {state_path}")
    except Exception as e:
        error_msg = f"Failed to create .gitkeep file {state_path}: {str(e)}"
        errors.append(error_msg)
        print(error_msg, file=sys.stderr)

    return {
        "created_directories": created_directories,
        "created_files": created_files,
        "errors": errors,
        "status": "success" if not errors else "partial"
    }

def main():
    """Main entry point for the script."""
    print("=" * 60)
    print("Creating project directory structure...")
    print("=" * 60)

    result = create_structure()

    print("\n" + "=" * 60)
    print("Directory structure creation summary:")
    print("=" * 60)
    print(f"Directories created: {len(result['created_directories'])}")
    print(f"Files created: {len(result['created_files'])}")
    print(f"Status: {result['status']}")

    if result['errors']:
        print(f"\nErrors encountered ({len(result['errors'])}):")
        for error in result['errors']:
            print(f"  - {error}")
        return 1

    # Print the created structure
    print("\nCreated directories:")
    for dir_path in result['created_directories']:
        print(f"  - {dir_path}")

    print("\nCreated .gitkeep files:")
    for file_path in result['created_files']:
        print(f"  - {file_path}")

    print("\n" + "=" * 60)
    print("Project directory structure created successfully!")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
