import os
from pathlib import Path

def main():
    """Create test directory structure for the project."""
    root = Path(__file__).resolve().parent
    tests_base = root / "tests"
    
    directories = [
        tests_base / "unit",
        tests_base / "integration",
    ]
    
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

if __name__ == "__main__":
    main()
