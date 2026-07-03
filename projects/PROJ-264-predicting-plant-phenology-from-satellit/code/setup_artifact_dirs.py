import os
import sys
from pathlib import Path

def main():
    """
    Creates the 'artifacts' and 'artifacts/models' directory structure
    required for the project.
    """
    project_root = Path(__file__).parent.parent
    artifacts_dir = project_root / "artifacts"
    models_dir = artifacts_dir / "models"

    # Create directories if they don't exist
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    # Create .gitkeep files to ensure directories are tracked by git
    (artifacts_dir / ".gitkeep").touch()
    (models_dir / ".gitkeep").touch()

    print(f"Created directories: {artifacts_dir}, {models_dir}")

if __name__ == "__main__":
    main()
