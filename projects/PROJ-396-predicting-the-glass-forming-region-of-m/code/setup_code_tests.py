import os
from pathlib import Path
from setup_directories import create_directory


def main():
    """Create the code/tests/ directory."""
    root = Path.cwd()
    target = root / "code" / "tests"
    create_directory(target)
    print(f"Created directory: {target}")


if __name__ == "__main__":
    main()
