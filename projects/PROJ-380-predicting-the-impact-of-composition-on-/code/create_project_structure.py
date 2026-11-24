"""
Script to create the required top‑level project directories for the
Predicting the Impact of Composition on the Shear Modulus of Bulk Metallic
Glasses project.

Directories created:
  - code/
  - data/
  - tests/
  - docs/
  - artifacts/

The platform owns a `state/` directory for internal bookkeeping, so this
script deliberately does **not** create a `state/` folder.
"""

import sys
from pathlib import Path

# Import the helper defined in the existing code/create_structure.py
from create_structure import create_directories
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main() -> None:
    """
    Entry point: create the required project directories under the repository root.
    """
    # The project root as defined by llmxive_toolkit
    project_root: Path = paths.root

    # List of directories that belong to the project (state/ is platform‑owned)
    dirs_to_create = ["code", "data", "tests", "docs", "artifacts"]

    log.info(f"Creating project directories under {project_root}")
    create_directories(project_root, dirs_to_create)

    # Verify creation (log warnings if any directory could not be made)
    for d in dirs_to_create:
        dir_path = project_root / d
        if dir_path.is_dir():
            log.info(f"✅ Created directory: {dir_path}")
        else:
            log.error(f"❌ Failed to create directory: {dir_path}")

if __name__ == "__main__":
    sys.exit(main())
