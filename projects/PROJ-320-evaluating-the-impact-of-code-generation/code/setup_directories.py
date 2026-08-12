import os
from pathlib import Path

def main():
    """
    Create the project directory structure for llmXive.
    This script ensures all required folders exist as per the project specification.
    """
    # Define the project root (assumed to be the directory containing this script's parent or cwd)
    # The task requires paths relative to the project root.
    # We will run this from the project root.
    root = Path.cwd()

    directories = [
        "code",
        "code/data",
        "code/analysis",
        "code/audit",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "reports/figures",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nSetup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
