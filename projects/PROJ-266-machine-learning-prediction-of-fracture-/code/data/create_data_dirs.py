import os
import sys
from pathlib import Path

def main():
    """
    Create the required data directory structure for the fracture toughness project.
    
    Creates:
        - data/raw: For raw input images and metadata
        - data/processed: For preprocessed images and split metadata
        - data/explainability: For attribution heatmaps and stability reports
    
    This task satisfies T004a verification:
        test -d data/raw && test -d data/processed && test -d data/explainability
    """
    # Define the base data directory relative to project root
    # The script is run from the project root, so we use relative paths
    base_dir = Path("data")
    
    directories = [
        base_dir / "raw",
        base_dir / "processed",
        base_dir / "explainability"
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    # Verify creation
    missing = [d for d in directories if not d.exists()]
    if missing:
        print(f"ERROR: Failed to create directories: {missing}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Successfully created {created_count} data directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
