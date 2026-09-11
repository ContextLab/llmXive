"""
Setup script to create the required project directory structure.
Creates all directories specified in tasks.md for the llmXive pipeline.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the standard project directory structure.
    Returns a list of created paths.
    """
    # Base directories as defined in tasks.md T001
    base_dirs = [
        "code",
        "data",
        "data/raw",
        "data/intermediate",
        "data/processed",
        "data/provenance",
        "data/results",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]

    created = []
    root = Path(".")

    for dir_path in base_dirs:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            # Verify it's actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
            created.append(str(full_path))

    return created

def main():
    """Entry point for directory creation."""
    print("Initializing project directory structure for PROJ-537...")
    try:
        created_dirs = create_directories()
        print(f"\nSuccessfully created/verified {len(created_dirs)} directories.")
        print("Structure ready for pipeline execution.")
        return 0
    except Exception as e:
        print(f"Error creating directories: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
