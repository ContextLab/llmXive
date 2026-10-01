import os
from pathlib import Path

def main():
    """
    Creates the project directory structure for llmXive PROJ-127.
    Implements Task T001a.
    """
    # Define the project root relative to the script location or current working directory
    # Assuming this script runs from the project root
    root = Path.cwd()

    # Define required directories per task T001a specification
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/models",
        "tests/unit",
        "tests/integration",
        "results",
    ]

    created = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            # Even if exists, ensure it is a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")

    print(f"Project structure initialized at: {root}")
    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All directories already exist.")

if __name__ == "__main__":
    main()
