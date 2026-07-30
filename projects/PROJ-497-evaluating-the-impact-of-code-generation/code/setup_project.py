import os
import sys
from pathlib import Path

def create_directory(path: Path) -> None:
    """Create a directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> None:
    """Create the standard project structure."""
    root = Path(__file__).resolve().parent.parent

    # Define the required directories relative to the project root
    directories = [
        root / "code",
        root / "data",
        root / "data" / "generated",
        root / "data" / "human",
        root / "data" / "processed",
        root / "results",
        root / "state",
        root / "tests",
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "tests" / "contract",
        root / "code" / "config",
    ]

    print(f"Setting up project structure at: {root}")
    for dir_path in directories:
        create_directory(dir_path)

    print("Project structure setup complete.")

if __name__ == "__main__":
    main()