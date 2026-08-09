import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-328.
    Ensures all required folders exist relative to the project root.
    """
    # Determine project root based on where this script is located
    # Assuming this script is at: code/setup_project_structure.py
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Define the project-specific root directory name
    project_name = "PROJ-328-predicting-the-impact-of-composition-on-"
    project_specific_root = project_root / project_name

    # Define required directories
    required_dirs = [
        "data",
        "data/raw",
        "data/processed",
        "data/outputs",
        "data/config",
        "data/checksums",
        "code",
        "tests",
        "models",
        "docs",
        "specs",
    ]

    print(f"Ensuring project structure at: {project_specific_root}")

    for dir_name in required_dirs:
        dir_path = project_specific_root / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  [OK] Created/Verified: {dir_path}")
        except OSError as e:
            print(f"  [ERROR] Failed to create {dir_path}: {e}")
            sys.exit(1)

    # Create placeholder __init__.py files to make them packages where appropriate
    # We treat 'code' and 'tests' as Python packages
    init_files = [
        project_specific_root / "code" / "__init__.py",
        project_specific_root / "tests" / "__init__.py",
        project_specific_root / "models" / "__init__.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"  [OK] Created placeholder: {init_file}")
        else:
            print(f"  [SKIP] Exists: {init_file}")

    # Create a .gitkeep in data directories to ensure they are tracked by git
    # even if empty
    data_subdirs = ["raw", "processed", "outputs", "config", "checksums"]
    for subdir in data_subdirs:
        keep_file = project_specific_root / "data" / subdir / ".gitkeep"
        if not keep_file.exists():
            keep_file.touch()
            print(f"  [OK] Created .gitkeep: {keep_file}")

    print("\nProject structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
