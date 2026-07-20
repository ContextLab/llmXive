import os
import sys
from pathlib import Path

def setup_directories(base_path: Path = None) -> None:
    """
    Creates the required data directory structure for the project.
    
    Directories created:
    - data/raw
    - data/processed
    - data/splits
    - results
    
    Args:
        base_path: Optional base path. Defaults to project root (parent of code/).
    """
    if base_path is None:
        # Determine project root: parent of the 'code' directory where this script lives
        base_path = Path(__file__).resolve().parent.parent

    data_dirs = [
        "data/raw",
        "data/processed",
        "data/splits",
        "results"
    ]

    created_count = 0
    for dir_path in data_dirs:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Setup complete. {created_count} new directories created.")

    # Verification: List contents of data/
    data_root = base_path / "data"
    if data_root.exists():
        print("\nVerification - Contents of data/:")
        for item in sorted(data_root.iterdir()):
            if item.is_dir():
                print(f"  [DIR] {item.name}")

if __name__ == "__main__":
    setup_directories()
