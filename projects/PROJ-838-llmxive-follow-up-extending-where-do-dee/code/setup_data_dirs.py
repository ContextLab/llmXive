"""
Script to initialize data directory structure for llmXive project.
Creates data/raw and data/processed directories with .gitkeep files.
"""
import os
from pathlib import Path
from config import ensure_directories

def main():
    """Initialize data directories and create .gitkeep placeholders."""
    # Define the directories to create
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/processed/graphs",
        "data/processed/figures"
    ]
    
    # Use ensure_directories from config to create them
    for dir_path in data_dirs:
        ensure_directories(dir_path)
        
        # Create .gitkeep file in each directory
        gitkeep_path = Path(dir_path) / ".gitkeep"
        gitkeep_path.touch()
        print(f"Created directory: {dir_path}")
        print(f"Created placeholder: {gitkeep_path}")
    
    print("\nData directory structure initialized successfully.")
    print("Directories ready for raw data ingestion and processed artifacts.")

if __name__ == "__main__":
    main()
