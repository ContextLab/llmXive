"""
Project structure setup module.
Creates the required directory tree for the statistical evaluation project.
"""
import os
from pathlib import Path


def create_project_structure(base_path: str = "projects/001-statistical-evaluation-of-dimensionality") -> None:
    """
    Create the project directory structure.

    Creates the following directories relative to base_path:
    - data/raw
    - data/processed
    - results
    - code
    - tests

    Args:
        base_path: The root path for the project structure. Defaults to the project name.
    """
    root = Path(base_path)
    
    # Define the directory structure
    directories = [
        "data/raw",
        "data/processed",
        "results",
        "code",
        "tests"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Create __init__.py files in code and tests to make them packages
    (root / "code" / "__init__.py").touch(exist_ok=True)
    (root / "tests" / "__init__.py").touch(exist_ok=True)
    
    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    print(f"Root: {root.resolve()}")


def main() -> None:
    """Main entry point for the script."""
    create_project_structure()


if __name__ == "__main__":
    main()
