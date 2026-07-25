"""
Directory creation and verification utility for llmXive project.
Creates the required project structure and verifies existence.
"""
import os
from pathlib import Path
from typing import List, Optional


def ensure_directories(
    base_path: Optional[Path] = None,
    directories: Optional[List[str]] = None
) -> List[Path]:
    """
    Ensure a list of directories exist under the base path.
    Creates them if they don't exist and verifies creation.

    Args:
        base_path: Root directory for the project (defaults to project root).
        directories: List of relative directory paths to create.

    Returns:
        List of created/verified Path objects.

    Raises:
        OSError: If a directory cannot be created or verified.
    """
    if base_path is None:
        base_path = Path(__file__).resolve().parent.parent

    if directories is None:
        # Default project structure based on tasks.md
        directories = [
            "code",
            "tests",
            "data/raw",
            "data/processed",
            "data/test",
            "specs",
            "docs",
            "specs/001-llmxive-drift-detection"
        ]

    created_paths = []

    for dir_path in directories:
        full_path = base_path / dir_path

        # Create directory if it doesn't exist
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)

        # Verify creation
        if not full_path.exists():
            raise OSError(f"Failed to create directory: {full_path}")

        if not full_path.is_dir():
            raise OSError(f"Path exists but is not a directory: {full_path}")

        created_paths.append(full_path)

    return created_paths


def main():
    """Main entry point for directory creation script."""
    import sys

    project_root = Path(__file__).resolve().parent.parent
    print(f"Project root: {project_root}")

    try:
        created = ensure_directories(project_root)
        print(f"Successfully created/verified {len(created)} directories:")
        for path in created:
            print(f"  - {path.relative_to(project_root)}")
        return 0
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
