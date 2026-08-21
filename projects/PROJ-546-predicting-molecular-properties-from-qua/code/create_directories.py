"""
Task T001: Initialize project structure.
Creates the required directory tree for the molecular properties prediction pipeline.
"""
import os
from pathlib import Path


def create_directories():
    """
    Create the full project directory structure as specified in T001.
    Paths are relative to the project root (current working directory).
    """
    # Define all required directories relative to the current working directory
    base_dirs = [
        "code",
        "data/raw",
        "data/optimized_geometries",
        "logs",
        "reports",
        "specs/546-predicting-molecular-properties/contracts",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    # Create directories
    created = []
    for dir_path in base_dirs:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        created.append(str(path))
        # Ensure __init__.py files exist for Python packages (code/, tests/)
        if dir_path.startswith("code") or dir_path.startswith("tests"):
            init_file = path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                created.append(str(init_file))

    return created


def main():
    """Entry point for directory initialization."""
    print("Initializing project directory structure...")
    created_paths = create_directories()
    print(f"Created {len(created_paths)} directories/files:")
    for p in sorted(created_paths):
        print(f"  - {p}")
    print("Project structure initialization complete.")


if __name__ == "__main__":
    main()