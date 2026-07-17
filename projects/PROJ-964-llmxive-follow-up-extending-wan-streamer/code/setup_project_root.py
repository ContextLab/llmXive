"""
Script to create the project root directory structure for llmXive follow-up.
This implements T005: Create the main project root directory.
"""
import os
import sys
from pathlib import Path


def setup_project_root(project_name: str = "PROJ-964-llmxive-follow-up-extending-wan-streamer") -> Path:
    """
    Create the project root directory.

    Args:
        project_name: Name of the project directory to create.

    Returns:
        Path to the created project root directory.

    Raises:
        FileExistsError: If the directory already exists (optional behavior).
    """
    # Define the project root path
    project_root = Path("projects") / project_name

    # Create the directory if it doesn't exist
    project_root.mkdir(parents=True, exist_ok=True)

    # Verify creation
    if not project_root.exists():
        raise RuntimeError(f"Failed to create project root directory: {project_root}")

    if not project_root.is_dir():
        raise RuntimeError(f"Path exists but is not a directory: {project_root}")

    return project_root


def main() -> None:
    """Main entry point for creating the project root directory."""
    project_name = "PROJ-964-llmxive-follow-up-extending-wan-streamer"
    print(f"Creating project root directory: projects/{project_name}/")

    try:
        project_root = setup_project_root(project_name)
        print(f"✓ Successfully created: {project_root}")
        print(f"  - Directory exists: {project_root.exists()}")
        print(f"  - Is directory: {project_root.is_dir()}")
    except Exception as e:
        print(f"✗ Error creating project root: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
