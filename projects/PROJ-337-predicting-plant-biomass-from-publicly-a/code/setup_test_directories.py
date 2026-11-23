"""
Setup script to create project test directories.

This script creates the directory structure required for organizing
unit, integration, and contract tests as defined in the project plan.
"""
import os
import sys
from pathlib import Path


def main() -> None:
    """Create test directories: unit, integration, contract."""
    # Determine project root based on the known directory structure
    # The script is located at code/setup_test_directories.py
    # The project root is the parent of 'code'
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Define the test directory structure relative to project root
    test_base = project_root / "tests"
    subdirectories = ["unit", "integration", "contract"]

    created_paths = []
    for subdir in subdirectories:
        target_path = test_base / subdir
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(target_path)
            print(f"Created directory: {target_path}")
        except PermissionError:
            print(f"Error: Permission denied creating {target_path}", file=sys.stderr)
            sys.exit(1)
        except OSError as e:
            print(f"Error: Failed to create {target_path}: {e}", file=sys.stderr)
            sys.exit(1)

    if not created_paths:
        print("Warning: No directories were created (all may already exist).")
    else:
        print(f"Successfully created {len(created_paths)} test directories.")

    # Create __init__.py files to make them proper Python packages
    for subdir in subdirectories:
        init_file = test_base / subdir / "__init__.py"
        try:
            init_file.touch(exist_ok=True)
            # Add a docstring to indicate purpose
            if init_file.stat().st_size == 0:
                init_file.write_text(
                    f'"""Test package for {subdir} tests."""\n'
                )
        except OSError as e:
            print(f"Warning: Could not create __init__.py in {test_base / subdir}: {e}", file=sys.stderr)

    print("Test directory setup complete.")


if __name__ == "__main__":
    main()