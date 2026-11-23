"""
Module to create the required directory structure for the project.
Ensures all necessary folders for data, tests, state, and docs exist.
"""
import os
from pathlib import Path
from typing import List

# Define the directory structure relative to the project root
# Based on tasks.md: T001a, T001b, T004
DIRECTORIES_TO_CREATE = [
    # Root directories (T001a)
    "code",
    "data",
    "tests",
    "state",
    "docs",
    # Data subdirectories (T001b, T004)
    "data/raw",
    "data/processed",
    # Test subdirectories (T001b)
    "tests/contract",
    "tests/unit",
    "tests/integration",
    # State subdirectories (T004 - implied for checksums storage)
    "state/checksums",
]

def create_directories(root_dir: Path) -> List[str]:
    """
    Create all required directories under the given root directory.
    
    Args:
        root_dir: The project root path.
        
    Returns:
        List of paths that were created or verified.
    """
    created_or_verified = []
    for dir_name in DIRECTORIES_TO_CREATE:
        target_path = root_dir / dir_name
        target_path.mkdir(parents=True, exist_ok=True)
        created_or_verified.append(str(target_path))
    return created_or_verified

def main():
    """
    Entry point to create the directory structure.
    Assumes the script is run from the project root or receives the root as an argument.
    """
    # Determine project root: usually the parent of the 'code' directory where this script lives
    # Or we can use the current working directory if run as `python code/setup_directories.py`
    # Given the task context, we assume the script is run from the project root.
    root = Path.cwd()
    
    print(f"Creating directory structure in: {root}")
    created_paths = create_directories(root)
    
    for p in created_paths:
        print(f"  - {p}")
    
    print(f"Successfully created/verified {len(created_paths)} directories.")

if __name__ == "__main__":
    main()
