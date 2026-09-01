import os
import sys
from pathlib import Path

# Define the directory structure required by the project
# Based on tasks.md and existing code references
DIRECTORIES = [
    "code/src",
    "code/tests",
    "code/tests/unit",
    "code/tests/integration",
    "code/data",
    "code/data/raw",
    "code/data/derived",
    "code/data/gold_standard",
    "code/artifacts",
    "code/specs",
    "code/specs/001-gene-regulation",
    "code/specs/001-gene-regulation/contracts",
    "code/config",
    "code/scripts",
]

def setup_directories():
    """
    Creates the project directory structure as defined in DIRECTORIES.
    Prints status to stdout and logs errors to stderr.
    """
    project_root = Path(__file__).parent.resolve()
    created_count = 0
    skipped_count = 0

    for dir_path in DIRECTORIES:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.exists() and full_path.is_dir():
                created_count += 1
        except Exception as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)

    print(f"Project structure setup complete. {created_count} directories ready.")
    return created_count

if __name__ == "__main__":
    setup_directories()
