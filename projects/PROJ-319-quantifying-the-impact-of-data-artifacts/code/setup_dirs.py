"""
Project directory initialization utilities.
Creates the standard project folder structure required for the pipeline.
"""
import os
import sys
from pathlib import Path
from typing import List


def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the script is run from the repository root or code/ subdirectory.
    """
    current = Path.cwd()
    # If running from code/, go up one level
    if current.name == "code":
        return current.parent
    # If running from root, return current
    if (current / "tasks.md").exists():
        return current
    # Fallback: look for tasks.md upwards
    for parent in current.parents:
        if (parent / "tasks.md").exists():
            return parent
    # Default to current if nothing found
    return current


def create_directories() -> None:
    """
    Create the standard project directory structure.
    
    Directories created:
    - code/, code/synthetic, code/metrics, code/analysis, code/io
    - data/raw, data/synthetic, data/processed, data/validation
    - tests/unit, tests/contract, tests/integration
    - logs
    """
    root = get_project_root()
    
    # Define relative paths based on tasks.md T001a
    dirs_to_create = [
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
    
    created_count = 0
    for rel_path in dirs_to_create:
        full_path = root / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")
    
    print(f"\nDirectory setup complete. Created {created_count} new directories.")
    print(f"Project root: {root}")


def main() -> None:
    """CLI entry point for directory creation."""
    print("Initializing project directories...")
    create_directories()
    print("Done.")


if __name__ == "__main__":
    main()
