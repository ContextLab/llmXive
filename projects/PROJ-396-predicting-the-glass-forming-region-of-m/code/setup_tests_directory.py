import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """Create the 'tests' directory."""
    root = Path(__file__).resolve().parent.parent
    tests_dir = root / "tests"
    create_directory(tests_dir)
    print(f"Created directory: {tests_dir}")

if __name__ == "__main__":
    main()
