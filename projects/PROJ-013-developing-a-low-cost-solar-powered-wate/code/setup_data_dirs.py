"""
Setup script for creating the required data directory structure.
Creates data/raw/, data/processed/, and data/plots/ directories.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the standard data directory structure."""
    # Determine project root (parent of the 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    plots_dir = data_dir / "plots"

    directories = [raw_dir, processed_dir, plots_dir]

    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

    # Also ensure data/raw/nist_materials.json exists if it doesn't,
    # though T011/T012 should handle the content. We just ensure the folder is there.
    # The task specifically asks for the directory structure.
    
    print(f"\nData directory structure ready at: {data_dir}")
    print(f"  - raw: {raw_dir}")
    print(f"  - processed: {processed_dir}")
    print(f"  - plots: {plots_dir}")

if __name__ == "__main__":
    main()