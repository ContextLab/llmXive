"""
Script to create the required directory structure for the llmXive project.
This ensures all necessary folders exist for data, results, state, contracts, logs, docs, and source code.
"""
import os
from pathlib import Path


def create_directory_structure():
    """
    Creates the full directory structure required by the project.
    This includes data directories, results, state, contracts, logs, docs,
    and the source code structure with submodules.
    """
    # Define all required directories relative to the project root
    # Assuming this script is run from the project root or code/scripts/
    # We will resolve paths relative to the script's parent directory (code/)
    base_dir = Path(__file__).resolve().parent.parent

    directories = [
        # Data directories
        "data/raw",
        "data/processed",
        
        # Output and state directories
        "results",
        "state",
        
        # Contract definitions
        "contracts",
        
        # Logging and documentation
        "logs",
        "docs",
        
        # Source code structure
        "src",
        "src/data",
        "src/graphs",
        "src/metrics",
        "src/analysis",
        "src/utils",
        "src/data_ingestion",
        
        # Test directories
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(base_dir)}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path.relative_to(base_dir)}")

    print(f"\nDirectory structure creation complete. Created {created_count} new directories.")
    return True


if __name__ == "__main__":
    create_directory_structure()