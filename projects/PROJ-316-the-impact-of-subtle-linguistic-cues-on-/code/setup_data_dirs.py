"""
Setup script to create the required data directory structure.
Creates data/raw, data/processed, and data/derived directories.
"""
import os
from pathlib import Path


def setup_data_directories():
    """Create the data directory structure if it doesn't exist."""
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"

    directories = [
        data_dir / "raw",
        data_dir / "processed",
        data_dir / "derived",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified: {directory}")

    # Create .gitkeep files to ensure directories are tracked by git
    for directory in directories:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# Keep this directory in git\n")
            print(f"Created: {gitkeep}")

    return True


if __name__ == "__main__":
    success = setup_data_directories()
    if success:
        print("Data directory structure setup complete.")
    else:
        print("Failed to setup data directory structure.")
        exit(1)