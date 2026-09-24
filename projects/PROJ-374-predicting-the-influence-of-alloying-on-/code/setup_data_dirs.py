"""
Script to setup the data directory structure for the project.
Creates data/raw/ and data/processed/ directories.
"""
import os
from pathlib import Path

def main():
    # Determine project root (assuming script is in code/)
    project_root = Path(__file__).resolve().parent.parent
    
    # Define data directories
    data_raw = project_root / "data" / "raw"
    data_processed = project_root / "data" / "processed"
    
    # Create directories if they don't exist
    data_raw.mkdir(parents=True, exist_ok=True)
    data_processed.mkdir(parents=True, exist_ok=True)
    
    print(f"Created directory: {data_raw}")
    print(f"Created directory: {data_processed}")

if __name__ == "__main__":
    main()