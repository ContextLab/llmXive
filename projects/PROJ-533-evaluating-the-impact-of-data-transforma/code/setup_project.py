import os
from pathlib import Path

def main():
    """
    Creates the project directory structure as specified in T001.
    Command equivalent: mkdir -p code/utils data/raw data/processed results/type1_error results/power results/aggregated results/checkpoints tests/unit tests/integration
    """
    # Define the root directory (current working directory)
    root = Path.cwd()

    # Define all required relative paths based on the task description
    directories = [
        "code/utils",
        "data/raw",
        "data/processed",
        "results/type1_error",
        "results/power",
        "results/aggregated",
        "results/checkpoints",
        "tests/unit",
        "tests/integration"
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

    print(f"Project structure setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()