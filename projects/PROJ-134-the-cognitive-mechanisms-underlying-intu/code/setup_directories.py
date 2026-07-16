import os
import sys
from pathlib import Path

def create_required_directories():
    """
    Create the required directory structure for the project data.
    Specifically creates: data/raw/, data/processed/, data/logs/
    """
    base_path = Path(__file__).resolve().parent.parent
    data_root = base_path / "data"

    required_dirs = [
        data_root / "raw",
        data_root / "processed",
        data_root / "logs",
    ]

    created = []
    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)
        created.append(str(directory.relative_to(base_path)))
    
    return created

def main():
    """Entry point to create directories."""
    print("Creating required data directories...")
    created_dirs = create_required_directories()
    for d in created_dirs:
        print(f"  Created: {d}")
    print("Directory setup complete.")

if __name__ == "__main__":
    main()