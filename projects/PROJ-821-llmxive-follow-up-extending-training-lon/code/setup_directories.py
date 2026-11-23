import os
import sys
from pathlib import Path

def get_project_root() -> Path:
    """
    Returns the project root directory.
    Assumes the script is run from the repository root or a subdirectory.
    We look for a 'specs' or 'data' directory to anchor the root, or default to current.
    """
    current = Path.cwd()
    # Simple heuristic: if we are in a subdirectory, walk up until we find a marker
    # For this project, 'specs' or 'data' (created by T001a/b) are markers.
    # If not found, assume cwd is root.
    for parent in [current] + list(current.parents):
        if (parent / "specs").exists() or (parent / "data").exists():
            return parent
    return current

def create_directories(dirs: list[str]) -> None:
    """
    Creates a list of directory paths relative to the project root.
    Creates parent directories as needed.
    """
    root = get_project_root()
    for d in dirs:
        full_path = root / d
        full_path.mkdir(parents=True, exist_ok=True)
        # Ensure the directory actually exists for verification purposes
        if not full_path.exists():
            raise RuntimeError(f"Failed to create directory: {full_path}")

if __name__ == "__main__":
    # Define the directories required for this task and previous setup tasks
    # T001a: code/ (handled by create_directories if not exists)
    # T001b: data/
    # T001c: data/synthetic/
    # T001d: data/synthetic/raw/
    # T001e: data/synthetic/short_context/
    # T001f: data/results/
    # T001g: data/results/logs/
    # T001h: data/results/aggregated/
    # T001i: tests/
    # T001j: models/
    # T001k: data/assets/

    required_dirs = [
        "code",
        "data",
        "data/synthetic",
        "data/synthetic/raw",
        "data/synthetic/short_context",
        "data/results",
        "data/results/logs",
        "data/results/aggregated",
        "tests",
        "models",
        "data/assets"
    ]

    create_directories(required_dirs)
    print(f"Directories created successfully in: {get_project_root()}")
