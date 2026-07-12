import os
from pathlib import Path

def main():
    """
    Setup the required data directory structure for the project.
    Creates:
      - data/raw/
      - data/processed/
    Ensures these directories exist relative to the project root.
    """
    # Determine project root (assuming code/ is at root level)
    current_dir = Path(__file__).parent
    project_root = current_dir.parent

    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    # Create directories if they don't exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    print(f"Created data directory structure:")
    print(f"  - {raw_dir}")
    print(f"  - {processed_dir}")

if __name__ == "__main__":
    main()