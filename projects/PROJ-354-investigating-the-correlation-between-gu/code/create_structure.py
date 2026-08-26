"""
Project Structure Initialization Script.

This script creates the standard directory structure required for the
Gut Microbiome-Cognitive Correlation Study project as defined in the
implementation plan.

It ensures the existence of:
- code/: Source code modules
- data/: Raw and processed data storage
- results/: Analysis outputs, reports, and figures
- tests/: Unit and integration tests
"""
import os
from pathlib import Path

def main():
    """
    Create the project directory structure.

    This function creates the four primary top-level directories
    required by the project specification: code, data, results, and tests.
    It also creates necessary subdirectories to support the pipeline.
    """
    # Define the root directory (current working directory or project root)
    root = Path(".")

    # Define the required directory structure
    directories = [
        # Source code
        "code",
        "code/models",
        "code/utils",
        "code/validation",
        "code/tests", # For unit tests if kept in code/ or separate

        # Data storage
        "data",
        "data/raw",       # Raw downloaded data (e.g., .parquet)
        "data/processed", # Intermediate and final processed data
        "data/external",  # External reference data if needed

        # Results and outputs
        "results",
        "results/associations", # Statistical association outputs
        "results/sensitivity",  # Sensitivity analysis outputs
        "results/validation",   # Validation reports
        "results/plots",        # Generated figures

        # Tests
        "tests",
        "tests/unit",
        "tests/integration",
    ]

    created_count = 0
    existing_count = 0

    print(f"Initializing project structure at: {root.resolve()}")

    for dir_path in directories:
        full_path = root / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                created_count += 1
                print(f"Created directory: {dir_path}")
            else:
                existing_count += 1
                # Optional: Verify it's a directory
                if not full_path.is_dir():
                    raise NotADirectoryError(f"Path exists but is not a directory: {dir_path}")
        except PermissionError:
            print(f"Error: Permission denied creating directory: {dir_path}")
            return 1
        except Exception as e:
            print(f"Error creating directory {dir_path}: {e}")
            return 1

    print(f"\nStructure initialization complete.")
    print(f"  - New directories created: {created_count}")
    print(f"  - Existing directories found: {existing_count}")

    # Verify the critical top-level directories exist
    critical_dirs = ["code", "data", "results", "tests"]
    missing = [d for d in critical_dirs if not (root / d).exists()]

    if missing:
        print(f"\nERROR: Critical directories missing: {missing}")
        return 1

    print("\nAll critical directories verified.")
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
