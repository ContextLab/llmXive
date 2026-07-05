import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """Create the 'tests/integration' directory."""
    root = Path(__file__).resolve().parent.parent
    tests_dir = root / "tests"
    integration_dir = tests_dir / "integration"
    create_directory(integration_dir)
    print(f"Created directory: {integration_dir}")

if __name__ == "__main__":
    main()
