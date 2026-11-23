import os
from pathlib import Path
from typing import Union

def ensure_directory(path: Union[str, Path]) -> None:
    """
    Ensure the given directory path exists. Creates it if it doesn't.
    
    Args:
        path: The directory path to ensure exists.
    """
    dir_path = Path(path)
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """
    Main function to create the required data directory structure.
    Creates: data/stimuli/, data/processed/, data/measurements/, data/raw/
    """
    base_data_dir = Path("data")
    
    # Ensure the base data directory exists first
    ensure_directory(base_data_dir)
    
    # Define the required subdirectories
    subdirectories = [
        "stimuli",
        "processed",
        "measurements",
        "raw"
    ]
    
    for subdir in subdirectories:
        dir_path = base_data_dir / subdir
        ensure_directory(dir_path)
        print(f"Ensured directory: {dir_path}")

if __name__ == "__main__":
    main()