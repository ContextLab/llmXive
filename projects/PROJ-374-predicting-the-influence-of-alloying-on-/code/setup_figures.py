"""
Setup script to create the docs/figures/ directory structure.
This task (T009) ensures the directory exists for storing visualization outputs.
"""
import os
from pathlib import Path

def main():
    """Create the docs/figures/ directory if it does not exist."""
    # Determine project root (parent of code/)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    figures_dir = project_root / "docs" / "figures"
    
    if not figures_dir.exists():
        figures_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {figures_dir}")
    else:
        print(f"Directory already exists: {figures_dir}")
    
    # Verify the directory is accessible
    if figures_dir.is_dir():
        print(f"Successfully verified: {figures_dir} is a valid directory.")
    else:
        raise RuntimeError(f"Failed to create or verify directory: {figures_dir}")

if __name__ == "__main__":
    main()