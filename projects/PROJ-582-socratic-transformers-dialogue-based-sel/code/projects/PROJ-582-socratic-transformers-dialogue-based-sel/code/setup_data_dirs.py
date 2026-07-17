"""
Setup script to create the data directory structure for the Socratic Transformers project.

This script creates the following directory structure under the project root:
- data/raw/          : For raw downloaded datasets (GSM8K, MATH)
- data/processed/    : For processed intermediate data (static QA, dialogue tuples)
- data/results/      : For final experiment results, metrics, and logs

It also creates .gitkeep files in each directory to ensure they are tracked by git.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the data directory structure."""
    # Determine the project root relative to this script
    # The script is located at: projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/setup_data_dirs.py
    # We want to create directories relative to the project root:
    # projects/PROJ-582-socratic-transformers-dialogue-based-sel/
    
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    project_root = code_dir.parent
    
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    results_dir = data_dir / "results"
    
    directories = [data_dir, raw_dir, processed_dir, results_dir]
    
    print(f"Setting up data directories under: {data_dir}")
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {directory}")
        
        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = directory / ".gitkeep"
        gitkeep_path.write_text("# This directory is tracked by git\n")
        print(f"  Created: {gitkeep_path}")
    
    print("\nData directory structure setup complete.")
    print(f"  {raw_dir}/")
    print(f"  {processed_dir}/")
    print(f"  {results_dir}/")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
