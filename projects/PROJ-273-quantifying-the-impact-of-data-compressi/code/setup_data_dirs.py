import os
from pathlib import Path

def setup_data_directories():
    """
    Create the required data directory structure for the project.
    Creates: data/raw/, data/interim/, data/processed/, data/external/
    """
    base_dir = Path(__file__).resolve().parent.parent
    data_root = base_dir / "data"

    directories = [
        "raw",
        "interim",
        "processed",
        "external"
    ]

    created = []
    for dir_name in directories:
        dir_path = data_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        created.append(str(dir_path))
        print(f"Created directory: {dir_path}")

    return created

if __name__ == "__main__":
    setup_data_directories()
