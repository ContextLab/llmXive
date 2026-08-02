import os
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure for PROJ-181-predicting-species-distribution-shifts-u.
    Creates the root project folder and all required subdirectories as defined in tasks.md.
    """
    # Define the project root relative to the current working directory or script location
    # Assuming this script is run from the repository root, we create the project folder inside 'projects/'
    base_dir = Path.cwd()
    project_root = base_dir / "projects" / "PROJ-181-predicting-species-distribution-shifts-u"

    # Define the directory structure to create
    # Top-level directories
    top_level_dirs = [
        "code",
        "data",
        "tests",
        "metrics",
        "reports",
        "logs",
        "state",
        "contracts"
    ]

    # Nested data directories
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/artifacts"
    ]

    # Nested test directories
    test_dirs = [
        "tests/unit",
        "tests/integration"
    ]

    all_dirs = top_level_dirs + data_dirs + test_dirs

    created_count = 0
    skipped_count = 0

    print(f"Initializing project structure at: {project_root}")

    for dir_path in all_dirs:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.is_dir():
                created_count += 1
                print(f"  Created: {full_path.relative_to(base_dir)}")
            else:
                print(f"  Warning: Path exists but is not a directory: {full_path}")
        except PermissionError:
            print(f"  Error: Permission denied creating {full_path}")
        except Exception as e:
            print(f"  Error creating {full_path}: {e}")

    # Ensure __init__.py files exist in Python packages to make them importable
    # We create them in code/, tests/, and their subdirectories
    init_files = []
    for root_dir in ["code", "tests", "tests/unit", "tests/integration"]:
        full_path = project_root / root_dir
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            init_files.append(init_file)
            print(f"  Created: {init_file.relative_to(base_dir)}")

    print(f"\nSummary: {created_count} directories created, {len(init_files)} __init__.py files added.")
    print(f"Project root is ready at: {project_root}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
