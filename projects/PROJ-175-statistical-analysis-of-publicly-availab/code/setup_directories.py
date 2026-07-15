"""
Setup script to initialize the project directory structure.
Creates the required data subdirectories (raw, processed, final)
and ensures the code module structure is in place.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to this script's location
    # The script is at code/setup_directories.py, so root is parent of 'code'
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Define the required directory structure
    # Based on T004: data/ with raw/, processed/, final/
    # Based on existing structure: code/, tests/ (already created in T001a/b conceptually, but we ensure existence)
    
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "final",
        project_root / "code" / "data",
        project_root / "code" / "models",
        project_root / "code" / "evaluation",
        project_root / "code" / "utils",
        project_root / "tests" / "contract",
        project_root / "tests" / "integration",
        project_root / "tests" / "unit",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path.relative_to(project_root)}")

    # Ensure __init__.py files exist in code subdirectories to make them packages
    # This is crucial for imports like `from data.download import ...`
    init_files = [
        project_root / "code" / "__init__.py",
        project_root / "code" / "data" / "__init__.py",
        project_root / "code" / "models" / "__init__.py",
        project_root / "code" / "evaluation" / "__init__.py",
        project_root / "code" / "utils" / "__init__.py",
        project_root / "tests" / "__init__.py",
        project_root / "tests" / "contract" / "__init__.py",
        project_root / "tests" / "integration" / "__init__.py",
        project_root / "tests" / "unit" / "__init__.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created empty __init__.py: {init_file.relative_to(project_root)}")
        else:
            print(f"__init__.py exists: {init_file.relative_to(project_root)}")

    print(f"\nSetup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    exit(main())
