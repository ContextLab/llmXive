"""
Script to create the required project directory structure for the analysis pipeline
and verify that it matches the implementation plan.

It reuses the existing `setup_project_structure.py` script to create the folders,
then checks that all expected directories exist and that a `contracts/` directory
has not been created at the project root. Finally, it prints the directory tree
using `ls -R` for manual verification.
"""

import subprocess
from pathlib import Path

# Import the existing setup script
from setup_project_structure import main as setup_main

from llmxive_toolkit import get_logger

log = get_logger(__name__)

# List of required directories relative to the project root
REQUIRED_DIRS = [
    Path("src/models"),
    Path("src/services"),
    Path("src/analysis"),
    Path("src/cli"),
    Path("src/utils"),
    Path("data/raw"),
    Path("data/processed"),
    Path("tests/unit"),
    Path("tests/integration"),
    Path("docs"),
]


def verify_structure(root: Path) -> None:
    """Ensure all required directories exist and `contracts/` does not."""
    for dir_path in REQUIRED_DIRS:
        full_path = root / dir_path
        if not full_path.is_dir():
            raise AssertionError(f"Required directory missing: {full_path}")

    contracts_path = root / "contracts"
    if contracts_path.exists():
        raise AssertionError("A `contracts/` directory must not be created at the project root.")


def main() -> int:
    """Create directories, verify them, and print the tree."""
    # Create the directory structure using the shared helper
    log.info("Creating project structure via setup_project_structure...")
    setup_main()

    # Verify the structure
    log.info("Verifying created directory structure...")
    verify_structure(Path.cwd())

    # Print the directory tree for visual confirmation
    log.info("Directory tree (ls -R):")
    subprocess.run(["ls", "-R"], check=True)

    log.info("Project structure created and verified successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
