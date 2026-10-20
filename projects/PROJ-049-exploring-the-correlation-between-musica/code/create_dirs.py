"""
Directory layout creation script for the project.

This script creates the required top‑level directories at the project root:
data/raw, data/processed, results, logs, code, and tests.

It uses the llmxive_toolkit `paths.root` helper to ensure the directories are
created relative to the repository root regardless of the current working
directory when the script is invoked.
"""

import sys
from pathlib import Path

# Import the project‑root path helper from the toolkit
from llmxive_toolkit import paths

def main() -> int:
    """
    Create the required project directories under the repository root.

    Returns
    -------
    int
        Exit code (0 for success).
    """
    # Resolve the root of the repository
    root_path: Path = paths.root

    # List of directories to create (relative to the root)
    required_dirs = [
        "data/raw",
        "data/processed",
        "results",
        "logs",
        "code",
        "tests",
    ]

    for rel_dir in required_dirs:
        dir_path = root_path / rel_dir
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Failed to create directory {dir_path}: {e}", file=sys.stderr)
            return 1

    # Success
    return 0

if __name__ == "__main__":
    sys.exit(main())