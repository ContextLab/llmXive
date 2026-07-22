"""
Setup data directory structure for the ball milling prediction project.
Creates the required directories under the data/ folder and ensures
placeholder files exist for verification.
"""
import os
import sys
from pathlib import Path


def setup_directories(base_dir: str = None) -> bool:
    """
    Create the required data directory structure.

    Args:
        base_dir: The root directory of the project. If None, uses the
                  current working directory.

    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    if base_dir is None:
        base_dir = Path.cwd()
    else:
        base_dir = Path(base_dir)

    # Define the required data directories
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/splits",
        "results",
        "data/fallback",
        "figures"
    ]

    success = True

    for dir_path in data_dirs:
        full_path = base_dir / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            # Create a .gitkeep file to ensure the directory is tracked by git
            gitkeep_path = full_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.touch()
            print(f"Created directory: {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}")
            success = False

    # Verify the structure
    if success:
        print("\nDirectory structure verification:")
        for dir_path in data_dirs:
            full_path = base_dir / dir_path
            if full_path.exists() and full_path.is_dir():
                print(f"  [OK] {dir_path}")
            else:
                print(f"  [FAIL] {dir_path}")
                success = False

    return success


if __name__ == "__main__":
    # Allow running with an optional base directory argument
    base = sys.argv[1] if len(sys.argv) > 1 else None
    if setup_directories(base):
        print("\nSetup completed successfully.")
        sys.exit(0)
    else:
        print("\nSetup failed.")
        sys.exit(1)
