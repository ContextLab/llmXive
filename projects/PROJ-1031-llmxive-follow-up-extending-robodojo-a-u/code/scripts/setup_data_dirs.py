import os
from pathlib import Path

def main():
    """
    Creates the required directory structure for the RoboDojo extension project:
    - code/data/raw/
    - code/data/interim/
    - code/data/processed/
    - code/data/final/
    """
    # Determine the base directory relative to the script location
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent  # Goes up from scripts/ to project root

    data_base = project_root / "code" / "data"
    
    directories = [
        data_base / "raw",
        data_base / "interim",
        data_base / "processed",
        data_base / "final"
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()
