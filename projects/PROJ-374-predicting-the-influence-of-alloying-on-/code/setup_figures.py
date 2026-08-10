"""
Setup script to create the docs/figures/ directory structure.
Ensures the directory exists for storing visualization outputs.
"""
import os
from pathlib import Path

def main():
    """Create the docs/figures/ directory if it doesn't exist."""
    # Determine project root (assuming script is in code/)
    project_root = Path(__file__).resolve().parent.parent
    figures_dir = project_root / "docs" / "figures"
    
    # Create directory if it doesn't exist
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Ensured directory exists: {figures_dir}")

if __name__ == "__main__":
    main()
