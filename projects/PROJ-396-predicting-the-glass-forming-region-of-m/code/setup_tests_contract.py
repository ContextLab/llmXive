import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """Create the 'tests/contract' directory."""
    root = Path(__file__).resolve().parent.parent
    tests_dir = root / "tests"
    contract_dir = tests_dir / "contract"
    create_directory(contract_dir)
    print(f"Created directory: {contract_dir}")

if __name__ == "__main__":
    main()
