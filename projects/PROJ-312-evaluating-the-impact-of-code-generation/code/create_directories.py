import os
from pathlib import Path

def main():
    """
    Creates the required directory structure for the project.
    """
    base_dir = Path("projects/PROJ-312-evaluating-the-impact-of-code-generation")
    
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/spot_check",
        "tests",
        "contracts",
        "artifacts",
        "state"
    ]

    for dir_path in dirs:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

if __name__ == "__main__":
    main()
