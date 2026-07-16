"""
Creates the required directory structure for the llmXive research pipeline.

This script implements task T001c by creating:
- data/raw/
- data/processed/
- output/results/
- output/figures/

These directories are essential for storing raw observational data, 
processed datasets, analysis results, and visualization figures.
"""
import os
from pathlib import Path


def create_directories():
    """Create the standard directory structure for the project."""
    base_path = Path(".")
    
    # Define directory structure
    directories = [
        "data/raw",
        "data/processed",
        "output/results",
        "output/figures",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nTotal directories created: {created_count}")
    print("Directory structure ready for data ingestion and analysis.")
    
    # Verify structure
    print("\nVerification of directory structure:")
    for dir_path in directories:
        full_path = base_path / dir_path
        status = "✓" if full_path.exists() and full_path.is_dir() else "✗"
        print(f"  {status} {dir_path}")
    
    return created_count


def main():
    """Entry point for the directory creation script."""
    print("=== llmXive Research Pipeline - Directory Setup ===")
    print("Task: T001c - Create data/ and output/ directory structure")
    print("=" * 50)
    
    create_directories()
    
    print("\n" + "=" * 50)
    print("Setup complete. Ready for data download and processing.")


if __name__ == "__main__":
    main()