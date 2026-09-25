import os
import sys
from pathlib import Path

def create_directories():
    """Create the project directory structure as defined in T001."""
    base = Path(__file__).parent.parent
    dirs = [
        "code",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs/figures",
        "state",
    ]
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {base / d}")

def main():
    create_directories()
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
