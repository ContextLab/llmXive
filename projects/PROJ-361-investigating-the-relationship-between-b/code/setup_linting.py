import os
import sys
from pathlib import Path

def check_file_exists(path: str) -> bool:
    """Check if a file exists at the given path."""
    return os.path.isfile(path)

def main():
    """Verify that linting configuration files exist."""
    base_dir = Path(__file__).parent
    config_files = [
        base_dir / ".flake8",
        base_dir / "pyproject.toml",
        base_dir / "mypy.ini",
    ]

    missing = []
    for file_path in config_files:
        if not check_file_exists(str(file_path)):
            missing.append(file_path.name)

    if missing:
        print(f"Error: Missing configuration files: {', '.join(missing)}")
        sys.exit(1)

    print("All linting configuration files are present.")
    sys.exit(0)

if __name__ == "__main__":
    main()
