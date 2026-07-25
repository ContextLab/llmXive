import os
import sys
from pathlib import Path

def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: The directory path to ensure exists.

    Returns:
        True if the directory exists or was created successfully, False otherwise.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main() -> int:
    """
    Main entry point for creating project directories.
    Creates the standard directory structure for the project.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Define the project root relative to repository root
    project_root = Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala")

    # Define the required directories
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests",
        project_root / "results",
    ]

    print(f"Creating project structure in: {project_root}")
    success = True

    for directory in directories:
        if ensure_directory(directory):
            print(f"Created: {directory}")
        else:
            success = False
            print(f"Failed to create: {directory}")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())