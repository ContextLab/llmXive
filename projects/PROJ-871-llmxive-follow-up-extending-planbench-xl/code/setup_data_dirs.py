import os
import sys
from pathlib import Path

from utils.config import get_path


def main() -> None:
    """
    Setup the data directory structure for the project.
    Creates:
      - data/raw
      - data/derived
      - data/logs
      - data/results
    """
    # Ensure the project root is in sys.path for imports if running as script
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Get the base data directory path from config
    try:
        data_dir = get_path("data")
    except KeyError:
        # Fallback to constructing path relative to project root if config key missing
        data_dir = project_root / "data"

    # Define subdirectories to create
    subdirs = ["raw", "derived", "logs", "results"]

    for subdir in subdirs:
        dir_path = data_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    print("Data directory structure setup complete.")


if __name__ == "__main__":
    main()
