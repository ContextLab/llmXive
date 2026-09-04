"""
Setup script to create the required data directory structure for the llmXive project.
Creates data/raw/, data/processed/, and data/results/ directories.
"""
import os
import sys
from pathlib import Path


def create_data_directories(base_dir: Path) -> None:
    """
    Create the standard data directory structure.

    Args:
        base_dir: The project root directory path.
    """
    data_dirs = [
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "results",
    ]

    for dir_path in data_dirs:
        if not dir_path.exists():
          dir_path.mkdir(parents=True, exist_ok=True)
          print(f"Created directory: {dir_path}")
        else:
          print(f"Directory already exists: {dir_path}")


def main() -> None:
    """Entry point for the setup_data_dirs script."""
    # Determine project root (assuming script is in code/)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    print(f"Project root: {project_root}")
    create_data_directories(project_root)
    print("Data directory setup complete.")


if __name__ == "__main__":
    main()