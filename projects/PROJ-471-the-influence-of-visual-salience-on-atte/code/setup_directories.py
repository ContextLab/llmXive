"""
T001a: Create Directory Structure
Ensures all required project directories exist.
"""
import os
from pathlib import Path

def create_directories():
    """Create the standard project directory structure."""
    # Base project root is assumed to be the parent of this file's directory
    # or the current working directory if run as a script.
    # We use the project root relative to the script location for safety.
    base_dir = Path(__file__).resolve().parent.parent

    directories = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    create_directories()
