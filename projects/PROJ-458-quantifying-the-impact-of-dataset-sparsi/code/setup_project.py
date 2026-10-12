"""Setup project layout for the dataset sparsity impact pipeline.

This script creates the required directory structure and writes a
`project_structure.txt` file that recursively lists all created
directories relative to the project root.

Directories created:
  - code/
  - data/raw/
  - data/processed/
  - data/results/
  - data/metadata/
  - tests/unit/
  - tests/integration/
  - docs/

The script is idempotent: running it multiple times will not raise
errors and will overwrite ``project_structure.txt`` with the current
layout.
"""

import os
from pathlib import Path
from llmxive_toolkit import paths

def _create_directories(root: Path, dirs):
    """Create each directory in ``dirs`` under ``root``."""
    for rel_dir in dirs:
        dir_path = root / rel_dir
        dir_path.mkdir(parents=True, exist_ok=True)

def _list_directories(root: Path):
    """Return a string with a recursive, sorted list of directories."""
    lines = []

    def _walk(current: Path, prefix: str = ""):
        for child in sorted(current.iterdir()):
            if child.is_dir():
                rel = child.relative_to(root)
                lines.append(str(rel) + "/")
                _walk(child, prefix + "  ")

    _walk(root)
    return "\n".join(lines)

def main():
    # Define the required project layout (relative to the project root)
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "data/metadata",
        "tests/unit",
        "tests/integration",
        "docs",
    ]

    # The root path is provided by llmxive_toolkit.paths
    project_root = paths.root

    # Create directories
    _create_directories(project_root, required_dirs)

    # Generate a recursive directory listing
    structure_listing = _list_directories(project_root)

    # Write the listing to ``project_structure.txt`` at the project root
    output_file = project_root / "project_structure.txt"
    output_file.write_text(structure_listing, encoding="utf-8")

    print(f"Project layout established. Listing written to {output_file}")

if __name__ == "__main__":
    main()