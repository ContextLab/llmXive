"""
Script to create the data directory for the project.
This script ensures the existence of the data directory at the specified path.
"""
import os
from pathlib import Path

def main():
    """
    Creates the data directory if it does not exist.
    """
    # Define the project root relative to this script's location
    # Script is at code/scripts/, project root is code/
    script_dir = Path(__file__).resolve().parent
    code_dir = script_dir.parent
    data_dir = code_dir / "data"

    # Create the directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)

    # Create a .gitkeep file to ensure the directory is tracked by git
    gitkeep_file = data_dir / ".gitkeep"
    gitkeep_file.write_text("# Data directory for molecular toxicity project\n")

    print(f"Data directory created at: {data_dir}")
    return 0

if __name__ == "__main__":
    exit(main())
