import os
import sys
from pathlib import Path

def main():
    """
    Creates the standard project directory structure for llmXive.
    This script ensures all required directories exist at the project root.
    """
    # Define the project root (current working directory where script is run)
    # We assume the script is run from the project root.
    project_root = Path.cwd()

    # Define the required directory structure
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/analysis",
        "models",
        "analysis",
        "tests",
        "docs"
    ]

    created_count = 0
    existing_count = 0

    print(f"Creating project structure in: {project_root}")

    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {dir_path}")
            created_count += 1
        else:
            existing_count += 1
            # print(f"  Exists: {dir_path}")

    print(f"Project structure setup complete. Created {created_count} directories, {existing_count} already existed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())