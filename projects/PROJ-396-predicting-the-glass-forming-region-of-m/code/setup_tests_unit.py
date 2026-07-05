import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """Create the 'tests/unit' directory."""
    root = Path(__file__).resolve().parent.parent
    tests_dir = root / "tests"
    unit_dir = tests_dir / "unit"
    create_directory(unit_dir)
    print(f"Created directory: {unit_dir}")

if __name__ == "__main__":
    main()
