"""
Script to create the required data directory structure for the project.
Creates:
  - data/
  - data/raw/
  - data/processed/graphs/
  - data/processed/conductivities/
  - data/processed/model_outputs/
"""
import os
import sys
from pathlib import Path

def create_data_directories():
    """Create the standard data directory structure."""
    base_path = Path("data")
    
    directories = [
        base_path,
        base_path / "raw",
        base_path / "processed" / "graphs",
        base_path / "processed" / "conductivities",
        base_path / "processed" / "model_outputs",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"\nData directory structure setup complete. Created {created_count} new directories.")
    return True

def main():
    """Entry point for the script."""
    try:
        success = create_data_directories()
        if success:
            print("SUCCESS: Data directories created successfully.")
            sys.exit(0)
        else:
            print("FAILED: Error creating data directories.")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
