import os
import sys
from pathlib import Path
from typing import List
from config import DATA_DIR, PROJECT_ROOT, LOG_DIR, ERRORS_DIR, MODELS_DIR, REPORTS_DIR

def create_directories() -> List[Path]:
    """
    Create the required project directory structure.
    Returns a list of created directory paths.
    """
    dirs_to_create: List[Path] = [
        PROJECT_ROOT / "code",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "curated",
        PROJECT_ROOT / "data" / "artifacts",
        PROJECT_ROOT / "data" / "logs",
        PROJECT_ROOT / "models",
        PROJECT_ROOT / "reports",
        PROJECT_ROOT / "errors",
        PROJECT_ROOT / "contracts",
        PROJECT_ROOT / "figures",
    ]

    created: List[Path] = []
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_path)
        elif dir_path.is_dir():
            created.append(dir_path)
        else:
            raise FileExistsError(f"Path exists but is not a directory: {dir_path}")

    return created

def create_init_files() -> None:
    """
    Create empty __init__.py files in code/ and tests/ to make them packages.
    """
    init_paths = [
        PROJECT_ROOT / "code" / "__init__.py",
        PROJECT_ROOT / "code" / "data" / "__init__.py",
        PROJECT_ROOT / "code" / "utils" / "__init__.py",
        PROJECT_ROOT / "code" / "models" / "__init__.py",
        PROJECT_ROOT / "code" / "validation" / "__init__.py",
        PROJECT_ROOT / "tests" / "__init__.py",
        PROJECT_ROOT / "tests" / "unit" / "__init__.py",
        PROJECT_ROOT / "tests" / "contract" / "__init__.py",
        PROJECT_ROOT / "tests" / "integration" / "__init__.py",
    ]

    for init_path in init_paths:
        init_path.parent.mkdir(parents=True, exist_ok=True)
        if not init_path.exists():
            init_path.touch()

def main() -> None:
    """
    Main entry point to set up the project structure.
    """
    print("Initializing project structure...")
    created_dirs = create_directories()
    print(f"Created/Verified directories: {len(created_dirs)}")
    for d in created_dirs:
        print(f"  - {d}")

    create_init_files()
    print("Created __init__.py files.")
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
