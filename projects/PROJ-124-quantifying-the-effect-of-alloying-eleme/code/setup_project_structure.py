"""
Project Structure Setup Script for PROJ-124.

This script creates the required directory structure for the
Quantifying the Effect of Alloying Elements on the Glass-Forming Ability
of Metallic Glasses project.

It ensures all necessary folders for code, data, state, output, tests,
and documentation exist before any other tasks are executed.
"""
import os
from pathlib import Path


def create_project_structure():
    """
    Create the full project directory structure as defined in the implementation plan.

    Creates directories for:
    - code/: Source modules (data, models, utils, config)
    - data/: Raw and processed data storage
    - state/: Pipeline state and artifact hashes
    - output/: Final results and candidates
    - tests/: Unit, integration, and contract tests
    - docs/: Paper drafts and reports
    """
    base_path = Path(".")

    # Define all required directories relative to the project root
    directories = [
        # Code modules
        "code/data",
        "code/models",
        "code/utils",
        "code/config",

        # Data storage
        "data/raw",
        "data/processed",

        # State and output
        "state",
        "output",

        # Testing
        "tests/contract",
        "tests/integration",
        "tests/unit",

        # Documentation
        "docs/paper",
        "docs/reports",
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            existing_count += 1

    print(f"\nProject structure setup complete.")
    print(f"  New directories created: {created_count}")
    print(f"  Directories already existing: {existing_count}")
    print(f"  Total directories managed: {len(directories)}")

    # Verify critical directories exist
    critical_dirs = [
        "code/data", "code/models", "code/utils", "code/config",
        "data/raw", "data/processed", "state", "output",
        "tests/contract", "tests/integration", "docs/paper"
    ]

    missing = []
    for dir_name in critical_dirs:
        if not (base_path / dir_name).exists():
            missing.append(dir_name)

    if missing:
        raise RuntimeError(f"Critical directories missing after setup: {missing}")

    return True


def main():
    """Entry point for the script."""
    print("Initializing project structure for PROJ-124...")
    try:
        create_project_structure()
        print("SUCCESS: Project structure is ready for implementation.")
    except Exception as e:
        print(f"FAILURE: {e}")
        raise


if __name__ == "__main__":
    main()
