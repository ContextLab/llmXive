"""
Creates the required artifact subdirectories for the project.

This script ensures the existence of:
- artifacts/models
- artifacts/reports
- artifacts/figures
"""
import os
from pathlib import Path

def main():
    """Create artifact directories if they do not exist."""
    project_root = Path(__file__).resolve().parent.parent
    artifacts_root = project_root / "artifacts"
    
    directories = [
        artifacts_root / "models",
        artifacts_root / "reports",
        artifacts_root / "figures",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified directory: {directory}")
    
    print("Artifact directory structure ready.")

if __name__ == "__main__":
    main()
