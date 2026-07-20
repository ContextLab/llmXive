import os
import sys
from pathlib import Path


def create_directories(root_dir: str = ".") -> None:
    """
    Create the standard project directory structure.

    Args:
        root_dir: Root directory where structure will be created (default: current)
    """
    path = Path(root_dir)
    if not path.exists():
        raise FileNotFoundError(f"Directory {root_dir} does not exist")

    # Define required directories
    directories = [
        "code",
        "code/data",
        "code/models",
        "code/utils",
        "data/raw",
        "data/processed",
        "output",
        "output/plots",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs",
    ]

    created_count = 0
    for dir_name in directories:
        full_path = path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists:  {full_path}")

    print(f"\nTotal directories created: {created_count}")


def main() -> None:
    """Main entry point for directory structure creation."""
    root = os.getenv("PROJECT_ROOT", ".")
    try:
        create_directories(root)
    except Exception as e:
        print(f"Error creating directories: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
