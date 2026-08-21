import os
import sys
from pathlib import Path

def ensure_directory(path_str: str) -> None:
    """
    Create a directory and its parents if they do not exist.
    Prints a confirmation message if the directory was created.
    """
    path = Path(path_str)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> None:
    """
    Main entry point to create required project directories.
    Specifically targets the directories required for T003:
    explanations/, state/, and tests/.
    """
    # Define the directories to create based on T003 requirements
    directories = [
        "explanations",
        "state",
        "tests"
    ]

    # Ensure they are created relative to the project root
    for dir_path in directories:
        ensure_directory(dir_path)

    print("Directory setup complete.")

if __name__ == "__main__":
    main()
