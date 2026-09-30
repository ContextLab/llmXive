"""
Module to create the project directory structure.
Implements T001: Create code and tests directory structure.
"""
import os
from pathlib import Path


def create_data_directories(base_dir: Path) -> None:
    """Create data subdirectories: raw, interim, processed."""
    data_dir = base_dir / "data"
    dirs = ["raw", "interim", "processed"]
    for d in dirs:
        (data_dir / d).mkdir(parents=True, exist_ok=True)


def create_test_directories(base_dir: Path) -> None:
    """Create test subdirectories: unit, integration."""
    tests_dir = base_dir / "tests"
    dirs = ["unit", "integration"]
    for d in dirs:
        (tests_dir / d).mkdir(parents=True, exist_ok=True)


def create_source_directories(base_dir: Path) -> None:
    """Create source directory."""
    (base_dir / "code").mkdir(parents=True, exist_ok=True)


def create_docs_directory(base_dir: Path) -> None:
    """Create docs directory."""
    (base_dir / "docs").mkdir(parents=True, exist_ok=True)


def create_all_directories(project_root: Path = None) -> None:
    """
    Create the full project directory structure required for T001.
    
    Creates:
    - code/
    - tests/unit/
    - tests/integration/
    - data/raw/
    - data/interim/
    - data/processed/
    - docs/ (bonus for future use)
    """
    if project_root is None:
        project_root = Path.cwd()
    
    create_source_directories(project_root)
    create_test_directories(project_root)
    create_data_directories(project_root)
    create_docs_directory(project_root)
    
    # Verify creation
    expected_dirs = [
        "code",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/interim",
        "data/processed",
        "docs"
    ]
    
    missing = []
    for d in expected_dirs:
        full_path = project_root / d
        if not full_path.exists():
            missing.append(str(full_path))
    
    if missing:
        raise RuntimeError(f"Failed to create directories: {missing}")


def main() -> None:
    """Entry point for script execution."""
    print("Creating project directory structure...")
    create_all_directories()
    print("Directory structure created successfully.")
    print("Created directories:")
    for d in ["code", "tests/unit", "tests/integration", "data/raw", "data/interim", "data/processed", "docs"]:
        print(f"  - {d}/")


if __name__ == "__main__":
    main()