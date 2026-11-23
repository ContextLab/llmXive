"""Initial project bootstrap.

This script is a thin wrapper around :func:`setup_directories.setup_directories`
and can be invoked directly (``python -m code.init_project``) to create the
required folder hierarchy.
"""

import sys
from pathlib import Path

from setup_directories import setup_directories


def main() -> None:
    """Create the standard layout and exit."""
    project_root = setup_directories()
    # Print the project root for convenience; useful in CI logs.
    print(f"Project root created at: {project_root}")


if __name__ == "__main__":
    main()
