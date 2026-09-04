import os
import sys
from pathlib import Path

# Define the directory structure relative to the project root
# Based on tasks.md: src/, tests/, data/, specs/001-gene-regulation/
# And Phase 2 T004 requirements: data/raw/, data/derived/, data/gold_standard/, artifacts/
DIRECTORIES = [
    "src",
    "src/lib",
    "src/services",
    "src/analysis",
    "src/cli",
    "src/models",
    "src/scripts",
    "tests",
    "tests/unit",
    "tests/integration",
    "data",
    "data/raw",
    "data/derived",
    "data/gold_standard",
    "artifacts",
    "specs",
    "specs/001-gene-regulation",
    "specs/001-gene-regulation/contracts",
    "config",
]

def setup_directories(root_path: Path = None) -> None:
    """
    Creates the necessary directory structure for the llmXive project.
    
    Args:
        root_path: The root directory of the project. Defaults to the current
                   working directory if None.
    """
    if root_path is None:
        root_path = Path.cwd()
    
    created_count = 0
    for dir_name in DIRECTORIES:
        dir_path = root_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        # Ensure the directory is writable (optional check, but good for robustness)
        if not os.access(dir_path, os.W_OK):
            raise PermissionError(f"Cannot write to directory: {dir_path}")
    
    print(f"Project structure setup complete. Created {created_count} new directories.")

def main():
    """Entry point for script execution."""
    setup_directories()

if __name__ == "__main__":
    main()
