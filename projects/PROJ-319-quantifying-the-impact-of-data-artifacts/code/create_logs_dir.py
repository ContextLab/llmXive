"""
Script to create the project 'logs' directory.
This satisfies task T001a4 which requires the existence of a logs/ directory.
"""

from pathlib import Path

# Use the llmxive_toolkit helper to get the absolute project root.
# This ensures the 'logs' directory is created at the repository root,
# regardless of where this script is executed from.
from llmxive_toolkit import paths


def create_logs_directory() -> None:
    """
    Ensure that the 'logs' directory exists at the project root.
    """
    # paths.root returns a pathlib.Path pointing to the project root.
    logs_dir: Path = paths.root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """
    Entry point for the script when run directly.
    """
    create_logs_directory()
    print("Logs directory created (or already existed).")


if __name__ == "__main__":
    main()