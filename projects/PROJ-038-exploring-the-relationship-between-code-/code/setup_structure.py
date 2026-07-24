import os
from pathlib import Path

def main():
    """Create the project directory structure."""
    dirs = [
        "code",
        "code/src",
        "code/tests",
        "code/data/raw",
        "code/data/processed",
        "code/data/results",
        "specs/001-code-complexity-bug-prediction"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    print("Directory structure created.")

if __name__ == "__main__":
    main()