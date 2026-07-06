import os
from pathlib import Path
from setup_directories import create_directory


def main():
    """Create the code/ directory at the repository root."""
    root = Path(__file__).resolve().parent.parent
    code_dir = root / "code"
    create_directory(code_dir)
    print(f"Created directory: {code_dir}")


if __name__ == "__main__":
    main()