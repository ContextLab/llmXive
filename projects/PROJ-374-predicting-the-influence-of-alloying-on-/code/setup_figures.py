"""
Script to setup the docs/figures/ directory structure.
This script ensures the directory exists for storing visualization outputs.
"""
import os
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    figures_dir = project_root / "docs" / "figures"
    
    # Create the directory if it doesn't exist
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Ensured directory exists: {figures_dir}")

if __name__ == "__main__":
    main()