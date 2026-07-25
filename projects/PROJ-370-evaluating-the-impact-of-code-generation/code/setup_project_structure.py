"""
Project structure setup script for llmXive research pipeline.
Creates the required directory hierarchy for data, code, tests, and results.
"""
import os
import sys
from pathlib import Path

def create_directories(base_path: Path = None) -> None:
    """
    Creates the standard project directory structure required by the pipeline.
    
    Directories created:
    - src/ (source code)
    - data/raw/ (raw fetched data)
    - data/derived/ (processed/derived data)
    - data/annotations/ (human annotations)
    - results/ (final reports and metrics)
    - tests/ (test suite)
    - specs/ (feature specifications)
    
    Args:
        base_path: Base directory to create structure in. Defaults to current working directory.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    # Define the required directory structure relative to base_path
    required_dirs = [
        "src",
        "data/raw",
        "data/derived",
        "data/annotations",
        "results",
        "tests",
        "specs"
    ]
    
    created_count = 0
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nProject structure setup complete. {created_count} new directories created.")
    print(f"Base path: {base_path}")

def main():
    """Main entry point for the script."""
    create_directories()

if __name__ == "__main__":
    main()
