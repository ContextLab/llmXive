"""
Directory structure initialization for the llmXive science pipeline.
Handles creation of all required project directories.
"""
import os
import sys
from pathlib import Path

# Define the standard directory structure relative to project root
REQUIRED_DIRS = [
    "code",
    "code/synthetic",
    "code/metrics",
    "code/analysis",
    "code/io",
    "data/raw",
    "data/synthetic",
    "data/processed",
    "data/validation",
    "tests/unit",
    "tests/contract",
    "tests/integration",
    "logs",
]

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the script is run from the project root or that 'code' exists relative to cwd.
    """
    current = Path.cwd()
    # If running from code/, go up one level
    if current.name == "code":
        return current.parent
    # If 'code' folder exists in current, assume current is root
    if (current / "code").is_dir():
        return current
    # Fallback: assume current is root
    return current

def create_directories() -> None:
    """
    Create all required project directories if they do not exist.
    Prints a log of created directories.
    """
    root = get_project_root()
    created_count = 0

    for dir_name in REQUIRED_DIRS:
        target_path = root / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {target_path}")
        else:
            # Ensure it's actually a directory
            if not target_path.is_dir():
                raise NotADirectoryError(
                    f"Expected a directory at {target_path}, but found a file."
                )

    print(f"Directory setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    create_directories()