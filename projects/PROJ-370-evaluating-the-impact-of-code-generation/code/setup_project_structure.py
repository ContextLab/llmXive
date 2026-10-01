"""
Project Structure Setup Script for llmXive pipeline.

This script creates the necessary directory structure for the project,
ensuring all required folders exist before other tasks begin.
"""

import os
import sys
from pathlib import Path


def create_directories(base_path: Path) -> None:
    """
    Create the standard project directory structure.

    Args:
        base_path: The root path where directories should be created.
    """
    # Define the required directories relative to the project root
    directories = [
        "src",
        "data/raw",
        "data/derived",
        "data/annotations",
        "results",
        "tests",
        "specs",
        # Subdirectories for better organization
        "src/extraction",
        "src/detection",
        "src/inference",
        "src/analysis",
        "src/reporting",
        "src/utils",
        "src/config",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "logs",
        "figures",
        "contracts",
    ]

    created_count = 0
    skipped_count = 0

    for dir_name in directories:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            skipped_count += 1
            # Only log if we want to be verbose about existing dirs
            # print(f"Directory already exists: {full_path}")

    print(f"\nSetup complete: {created_count} directories created, {skipped_count} already existed.")


def main() -> int:
    """
    Main entry point for the script.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Determine the project root (parent of the 'code' directory)
        current_file = Path(__file__).resolve()
        code_dir = current_file.parent
        project_root = code_dir.parent

        print(f"Project root: {project_root}")
        print("Creating project directory structure...")

        create_directories(project_root)

        # Verify creation by listing top-level directories
        print("\nVerifying directory structure:")
        top_level_dirs = ["src", "data", "tests", "results", "specs", "contracts", "logs", "figures"]
        for dir_name in top_level_dirs:
            full_path = project_root / dir_name
            if full_path.exists():
                print(f"  ✓ {dir_name}/")
            else:
                print(f"  ✗ {dir_name}/ (MISSING)")
                return 1

        return 0

    except Exception as e:
        print(f"Error during directory creation: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())