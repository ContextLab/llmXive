"""
Project structure initialization script.
Creates the required directory hierarchy for the plant defense allocation pipeline.
"""
import os
import sys
from pathlib import Path
from src.utils.setup_directories import setup_data_directories, main as setup_main

def create_directory_structure(base_path: Path = None) -> None:
    """
    Creates the project directory structure as per the implementation plan.
    
    Structure:
    code/
      src/
        utils/
        data/
        analysis/
        cli/
      tests/
        unit/
        integration/
        contract/
      scripts/
    data/
      raw/
      processed/
        trimmed/
        aligned/
        count_matrices/
      traits/
      manifests/
      synthetic/
      figures/
    specs/
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent
    
    # Define directories to create
    dirs_to_create = [
        # Source code structure
        base_path / "code" / "src" / "utils",
        base_path / "code" / "src" / "data",
        base_path / "code" / "src" / "analysis",
        base_path / "code" / "src" / "cli",
        
        # Test structure
        base_path / "code" / "tests" / "unit",
        base_path / "code" / "tests" / "integration",
        base_path / "code" / "tests" / "contract",
        
        # Scripts
        base_path / "code" / "scripts",
        
        # Data structure (handled by setup_data_directories, but defined here for clarity)
        base_path / "data" / "raw",
        base_path / "data" / "processed" / "trimmed",
        base_path / "data" / "processed" / "aligned",
        base_path / "data" / "processed" / "count_matrices",
        base_path / "data" / "traits",
        base_path / "data" / "manifests",
        base_path / "data" / "synthetic",
        base_path / "data" / "figures",
        
        # Specs
        base_path / "specs",
    ]
    
    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path.relative_to(base_path)}")
        else:
            print(f"Directory exists: {dir_path.relative_to(base_path)}")
    
    print(f"\nProject structure setup complete. Created {created_count} new directories.")

def main():
    """CLI entry point for directory creation."""
    print("Initializing project directory structure...")
    create_directory_structure()
    
    # Also run the data-specific setup from utils
    setup_main()
    
    print("All directories initialized successfully.")

if __name__ == "__main__":
    main()
