"""
Script to initialize the project directory structure for llmXive research pipeline.
Creates necessary subdirectories under data/ and outputs/ as defined in T001b.
"""
import os
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the project.
    Ensures all directories exist before proceeding with data generation.
    """
    base_path = Path(__file__).parent.parent
    
    directories = [
        "data/benchmarks",
        "data/benchmarks/raw",
        "data/benchmarks/processed",
        "data/generated",
        "data/coverage_reports",
        "data/processed",
        "outputs"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            existing_count += 1
            print(f"Already exists: {full_path}")
    
    print(f"\nDirectory setup complete.")
    print(f"Created: {created_count} new directories.")
    print(f"Existing: {existing_count} directories.")
    
    # Verify structure
    print("\nVerifying directory structure:")
    for dir_path in directories:
        full_path = base_path / dir_path
        if full_path.exists():
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} (MISSING)")
            raise RuntimeError(f"Failed to create {dir_path}")

if __name__ == "__main__":
    create_directories()