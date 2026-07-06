import os
from pathlib import Path

def main():
    """
    Create the required directory structure for the project.
    Creates:
      - data/raw/
      - data/derived/
      - code/
      - tests/
    """
    base_dir = Path(__file__).parent.parent
    
    directories = [
        base_dir / "data" / "raw",
        base_dir / "data" / "derived",
        base_dir / "code",
        base_dir / "tests",
    ]
    
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

if __name__ == "__main__":
    main()
