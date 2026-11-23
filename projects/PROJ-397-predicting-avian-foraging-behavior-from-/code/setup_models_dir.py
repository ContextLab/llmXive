"""
Initialize the models directory for the project.
Creates the directory structure and a .gitkeep file to ensure
the directory is tracked by git even when empty.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the models directory and .gitkeep file."""
    # Determine project root relative to this script location
    # The script is in code/, so project root is the parent of code/
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent

    models_dir = project_root / "models"

    # Create the directory if it doesn't exist
    models_dir.mkdir(parents=True, exist_ok=True)

    # Create .gitkeep file
    gitkeep_path = models_dir / ".gitkeep"
    gitkeep_path.touch()

    print(f"Created directory: {models_dir}")
    print(f"Created placeholder file: {gitkeep_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
