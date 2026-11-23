"""
Setup script to ensure all required project directories exist.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the standard directory structure."""
    root = Path(__file__).parent.parent
    
    dirs = [
        "code/data",
        "code/analysis",
        "code/reports",
        "code/utils",
        "code/tests",
        "code/scripts",
        "data/raw",
        "data/processed",
        "data/consent",
        "data/reports",
        "logs",
        "contracts",
    ]

    for d in dirs:
        path = root / d
        path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure tracking
        gitkeep = path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
    
    print(f"Directory structure verified/created at {root}")

def verify_structure():
    """Verify critical files exist."""
    root = Path(__file__).parent.parent
    critical_files = [
        "contracts/dataset.schema.yaml",
        "requirements.txt",
        "code/utils/config.py",
        "code/utils/logging.py",
        "code/data/models.py",
    ]
    
    missing = []
    for f in critical_files:
        if not (root / f).exists():
            missing.append(f)
    
    if missing:
        print(f"Warning: Missing critical files: {missing}")
        return False
    return True

def main():
    create_directories()
    if verify_structure():
        print("Setup complete.")
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
