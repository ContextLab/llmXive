import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required data directory structure:
    - data/raw/
    - data/simulated/
    - data/results/

    Places a .gitkeep file in each to ensure directories are tracked by git.
    """
    base_path = Path(__file__).resolve().parents[2]  # Project root
    data_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "simulated",
        base_path / "data" / "results",
    ]

    created_count = 0
    for dir_path in data_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

        # Ensure .gitkeep exists
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep in: {dir_path}")
        else:
            print(f".gitkeep already exists in: {dir_path}")

    print(f"Data directory setup complete. {created_count} new directories created.")
    return True

def main():
    """Entry point for script execution."""
    success = create_directories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()