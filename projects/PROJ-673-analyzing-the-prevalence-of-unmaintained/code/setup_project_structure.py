import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in the implementation plan.
    Executes the equivalent of:
    mkdir -p src/models src/services src/analysis src/cli src/utils data/raw data/processed tests/unit tests/integration docs
    """
    # Define the relative paths to create
    # Note: The plan mentions 'src/' but the existing API surface uses 'code/src/'
    # We will create the structure under 'code/' to align with the existing file paths provided in the context.
    base_dir = Path("code")
    directories = [
        "src/models",
        "src/services",
        "src/analysis",
        "src/cli",
        "src/utils",
        "src/config",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs",
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            existing_count += 1
            # Optional: print existing to verify structure if needed, but keep output clean
            # print(f"Directory already exists: {full_path}")

    print(f"Project structure ready. Created: {created_count}, Existing: {existing_count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())