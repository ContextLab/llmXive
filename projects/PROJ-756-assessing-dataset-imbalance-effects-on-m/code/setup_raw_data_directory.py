import os
import sys
from pathlib import Path

def create_raw_data_directory(base_path: Path) -> None:
    """
    Creates the raw data directory.
    Expected: data/raw/
    """
    raw_path = base_path / "data" / "raw"
    raw_path.mkdir(parents=True, exist_ok=True)
    print(f"Created raw data directory: {raw_path}")

def main() -> None:
    project_root = Path.cwd()
    project_id = "PROJ-756-assessing-dataset-imbalance-effects-on-m"
    base_path = project_root / "projects" / project_id
    create_raw_data_directory(base_path)

if __name__ == "__main__":
    main()
