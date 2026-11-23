"""
Script to create required sub‑directories under the `code/` package.
This satisfies task T001a1 by ensuring the directories:
`synthetic`, `metrics`, `analysis`, and `io` exist.
"""

from pathlib import Path

# Import the helper that determines the project root.
# This function is defined in `code/config.py`.
from code.config import get_project_root


def create_subdirectories() -> None:
    """
    Create the required sub‑directories inside the `code/` directory.
    """
    root = get_project_root()
    code_dir = root / "code"
    subdirs = ["synthetic", "metrics", "analysis", "io"]

    for sub in subdirs:
        dir_path = code_dir / sub
        dir_path.mkdir(parents=True, exist_ok=True)
        # Optional: log creation (stdout is captured by the runner)
        print(f"Created directory: {dir_path}")


def main() -> None:
    """Entry point for the script."""
    create_subdirectories()


if __name__ == "__main__":
    main()