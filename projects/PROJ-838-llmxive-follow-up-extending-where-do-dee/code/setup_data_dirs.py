"""
Setup script to initialize data directories.

This script creates the required directory structure for the llmXive pipeline:
- data/raw: For storing downloaded raw datasets (TELBench)
- data/processed: For storing processed artifacts (graphs, metrics, reports)

It uses the ensure_directories function from config.py to create these paths
and places .gitkeep files to ensure the directories are tracked by git.
"""
import os
from pathlib import Path
from config import ensure_directories


def main():
    """
    Initialize data directories and create .gitkeep files.
    
    Creates:
    - data/raw/.gitkeep
    - data/processed/.gitkeep
    - data/processed/graphs/.gitkeep (for intermediate DAGs)
    - data/processed/reports/.gitkeep (for final reports)
    
    Prints status messages for each operation.
    """
    print("Setting up data directories...")
    
    # Ensure base directories exist using the config utility
    ensure_directories()
    
    # Define the paths for the required directories
    base_path = Path("data")
    raw_path = base_path / "raw"
    processed_path = base_path / "processed"
    graphs_path = processed_path / "graphs"
    reports_path = processed_path / "reports"
    
    # Create directories if they don't exist
    for dir_path in [raw_path, processed_path, graphs_path, reports_path]:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created directory: {dir_path}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    gitkeep_content = "# This file ensures the directory is tracked by git.\n"
    
    gitkeep_files = [
        raw_path / ".gitkeep",
        processed_path / ".gitkeep",
        graphs_path / ".gitkeep",
        reports_path / ".gitkeep",
    ]
    
    for gitkeep_path in gitkeep_files:
        gitkeep_path.write_text(gitkeep_content)
        print(f"  Created .gitkeep: {gitkeep_path}")
    
    print("Data directory setup complete.")


if __name__ == "__main__":
    main()