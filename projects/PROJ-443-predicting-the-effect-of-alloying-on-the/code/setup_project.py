"""
Project structure setup script.
Creates the required directory structure for the HEA Elastic Modulus prediction project.
"""
import os
import sys
from pathlib import Path


def create_directories():
    """Create the standard project directory structure."""
    # Define the base directory (current working directory or specified path)
    base_dir = Path.cwd()

    # Define required directories relative to the project root
    # Based on tasks.md: src/, tests/, data/raw/, data/processed/, results/
    # Note: The task mentions 'src/' but the existing API surface uses 'code/' as the root.
    # We will create directories under 'code/' to match the existing file structure provided in the API surface.
    # The API surface shows files like 'code/src/data/fetch_oqmd.py', 'code/tests/unit/...'.
    # Therefore, we treat 'code' as the project root for this implementation to align with existing artifacts.
    
    # Adjusting paths to match the existing API surface structure (code/ is the root)
    project_root = base_dir / "code"
    
    directories = [
        project_root / "src",
        project_root / "tests",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
        project_root / "figures",
        project_root / "specs",
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")

    # Create __init__.py files to ensure they are recognized as Python packages
    init_files = [
        project_root / "src" / "__init__.py",
        project_root / "tests" / "__init__.py",
        project_root / "src" / "utils" / "__init__.py",
        project_root / "src" / "data" / "__init__.py",
        project_root / "src" / "features" / "__init__.py",
        project_root / "src" / "model" / "__init__.py",
        project_root / "src" / "models" / "__init__.py",
        project_root / "src" / "pipeline" / "__init__.py",
        project_root / "src" / "report" / "__init__.py",
        project_root / "tests" / "unit" / "__init__.py",
        project_root / "tests" / "integration" / "__init__.py",
    ]

    # Ensure subdirectories for __init__.py exist
    for init_file in init_files:
        init_file.parent.mkdir(parents=True, exist_ok=True)
        if not init_file.exists():
            init_file.touch()
            print(f"Created init file: {init_file}")
        else:
            print(f"Init file already exists: {init_file}")

    return created_count


def main():
    """Entry point for the script."""
    print("Setting up project structure...")
    created = create_directories()
    print(f"Setup complete. Created {created} new directories.")
    sys.exit(0)


if __name__ == "__main__":
    main()
