"""
Setup Data Directory Structure for llmXive Project.

This module creates the required directory structure for data storage:
- data/raw/: For immutable puzzle datasets
- data/processed/: For logs, results, and analysis outputs

This task implements T004 from the project plan.
"""

import os
import sys
from pathlib import Path
from typing import List


def setup_data_directories(root_dir: str = None) -> List[str]:
    """
    Create the required data directory structure.

    Args:
        root_dir: The project root directory. If None, uses the current
                  working directory.

    Returns:
        List of created directory paths as strings.

    Raises:
        OSError: If directory creation fails due to permissions or other OS errors.
    """
    if root_dir is None:
        root_dir = os.getcwd()

    root_path = Path(root_dir)

    # Define required directories relative to project root
    data_dirs = [
        root_path / "data",
        root_path / "data" / "raw",
        root_path / "data" / "processed",
    ]

    created_dirs = []

    for dir_path in data_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
        else:
            # Directory already exists, still track it for reporting
            created_dirs.append(str(dir_path))

    return created_dirs


def main():
    """
    Entry point for command-line execution.

    Creates the data directory structure and prints the paths created.
    """
    try:
        created = setup_data_directories()
        print("Successfully created/verified data directories:")
        for d in created:
            print(f"  - {d}")
        return 0
    except OSError as e:
        print(f"Error creating directories: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())