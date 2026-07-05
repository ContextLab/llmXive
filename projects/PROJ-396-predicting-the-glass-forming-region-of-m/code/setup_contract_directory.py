import os
from pathlib import Path
from setup_directories import create_directory, main as setup_main

def main():
    """Create the tests/contract/ directory."""
    root = Path(os.getcwd())
    contract_dir = root / "tests" / "contract"
    create_directory(contract_dir)
    print(f"Created directory: {contract_dir}")

if __name__ == "__main__":
    main()
