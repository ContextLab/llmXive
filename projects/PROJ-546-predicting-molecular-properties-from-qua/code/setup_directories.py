"""
Setup script to initialize the project directory structure for PROJ-546.
Creates the root project directory and all required subdirectories.
"""
import os
from pathlib import Path


def create_directories():
    """
    Create the full project directory hierarchy as specified in T001.
    All paths are relative to the project root.
    """
    # Define the base project directory
    project_root = Path("projects/PROJ-546-predicting-molecular-properties-from-qua")

    # Define all required directories relative to the project root
    directories = [
        # Core directories
        "code",
        "data/raw",
        "data/optimized_geometries",
        "logs",
        "reports",
        "contracts",
        "docs",
        
        # Test directories
        "tests/unit",
        "tests/integration",
        "tests/contract",
        
        # Additional standard directories (implied by project structure)
        "data/processed",
        "data/external",
        "scripts",
        "notebooks",
        "models",
    ]

    created_count = 0
    for dir_name in directories:
        full_path = project_root / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    # Create __init__.py files in Python packages to make them importable
    python_packages = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data",
        "data/raw",
        "data/optimized_geometries",
        "data/processed",
        "data/external",
        "logs",
        "reports",
        "contracts",
        "docs",
        "models",
        "scripts",
        "notebooks",
    ]

    for pkg in python_packages:
        init_path = project_root / pkg / "__init__.py"
        if not init_path.exists():
            init_path.write_text("")
            print(f"Created __init__.py: {init_path}")

    print(f"\nProject structure initialized successfully.")
    print(f"Total directories created: {created_count}")
    print(f"Project root: {project_root.absolute()}")
    return project_root


def main():
    """Main entry point for the script."""
    print("Initializing project structure for PROJ-546...")
    create_directories()
    print("Done.")


if __name__ == "__main__":
    main()
