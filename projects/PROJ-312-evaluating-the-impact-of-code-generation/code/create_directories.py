import os
from pathlib import Path

def main():
    """
    Create the required directory structure for the project.
    
    Creates:
    - data/raw/
    - data/processed/
    - data/spot_check/
    - artifacts/
    - tests/
    """
    project_root = Path(__file__).parent.parent
    base_dirs = [
        "data/raw",
        "data/processed",
        "data/spot_check",
        "artifacts",
        "tests"
    ]

    for dir_path in base_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

if __name__ == "__main__":
    main()