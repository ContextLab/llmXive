import os
from pathlib import Path

def main():
    """
    Creates the required directory structure for the RoboDojo data pipeline:
    - code/data/raw/
    - code/data/interim/
    - code/data/processed/
    - code/data/final/
    """
    base_dir = Path(__file__).resolve().parent.parent / "data"
    
    directories = [
        "raw",
        "interim",
        "processed",
        "final"
    ]
    
    for dir_name in directories:
        dir_path = base_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified: {dir_path}")

if __name__ == "__main__":
    main()