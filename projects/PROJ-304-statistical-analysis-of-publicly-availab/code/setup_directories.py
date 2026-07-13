import os
from pathlib import Path

def main():
    """
    Create the required directory structure for the project:
    - data/raw
    - data/processed
    - code
    - tests/unit
    - tests/integration
    """
    # Determine project root (parent of the code directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Define directories to create
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Setup complete. {created_count} new directory(ies) created.")
    return 0

if __name__ == "__main__":
    exit(main())
