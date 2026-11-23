"""
Project Structure Initialization Script for llmXive Follow-up.

This script creates the required directory structure for the project
as defined in plan.md and the task specifications.

Required Structure:
- projects/PROJ-1011-llmxive-follow-up-extending-researchstud/
  - code/
  - data/
    - raw/
    - processed/
    - results/
  - tests/
  - state/
"""

import os
import sys
from pathlib import Path


def main():
    """
    Create the project directory structure.

    This function ensures that all required directories exist:
    1. The main project directory
    2. Subdirectories: code, data (with raw, processed, results), tests, state
    3. Creates a .gitkeep file in each directory to ensure they are tracked by git

    Returns:
        int: 0 on success, 1 on failure
    """
    # Define the project root and structure
    project_root = Path("projects/PROJ-1011-llmxive-follow-up-extending-researchstud")
    directories = [
        project_root,
        project_root / "code",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "tests",
        project_root / "state",
    ]

    print(f"Creating project structure in: {project_root.absolute()}")

    success = True
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created: {directory}")

            # Create .gitkeep to ensure empty directories are tracked
            gitkeep = directory / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
                print(f"    - Created .gitkeep in {directory}")

        except OSError as e:
            print(f"  ✗ Failed to create {directory}: {e}")
            success = False

    if success:
        print("\nProject structure created successfully!")
        print(f"Root: {project_root}")
        print("Subdirectories: code, data/raw, data/processed, data/results, tests, state")
        return 0
    else:
        print("\nERROR: Some directories failed to create. Check permissions and disk space.")
        return 1


if __name__ == "__main__":
    sys.exit(main())