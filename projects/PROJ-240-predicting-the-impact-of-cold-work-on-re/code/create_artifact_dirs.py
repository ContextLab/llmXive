"""
Script to create the required artifact directories for the project.
Creates: artifacts/models, artifacts/reports, artifacts/figures
"""
import os
from pathlib import Path


def main():
    """Create artifact directories."""
    project_root = Path(__file__).parent.parent
    artifacts_root = project_root / "artifacts"
    
    directories = [
        artifacts_root / "models",
        artifacts_root / "reports",
        artifacts_root / "figures",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    print("All artifact directories created successfully.")


if __name__ == "__main__":
    main()
