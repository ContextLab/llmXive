"""
Setup script to create the required project directory structure.
This script ensures that data/raw, data/processed, data/models, code, and tests
directories exist under the project root.
"""
import os
import sys
from pathlib import Path

# Define the project root (assumed to be the parent of the 'code' directory)
# If running as __main__, determine root relative to this file
if __name__ == "__main__":
    # Script is located in code/, so root is parent of code/
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
else:
    # When imported, assume current working directory or explicit root
    PROJECT_ROOT = Path.cwd()

# Define relative paths to be created
DIRECTORIES = [
    "data/raw",
    "data/processed",
    "data/models",
    "code",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/perf",
    "contracts",
    "docs",
    "docs/reports",
    "specs",
]

def setup_directories():
    """Create the required directory structure."""
    created_count = 0
    existing_count = 0

    for rel_path in DIRECTORIES:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            existing_count += 1

    print(f"Setup complete. Created {created_count} new directories. {existing_count} already existed.")
    return created_count

if __name__ == "__main__":
    setup_directories()