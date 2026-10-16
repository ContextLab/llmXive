"""
Bootstrap script for the Visual Salience project.

This script creates the required project layout, writes a pinned
``requirements.txt`` file at the project root and prints a directory
tree as proof of successful setup.

The implementation lazily imports ``llmxive_toolkit.paths`` inside each
helper function so that test suites can monkey‑patch ``paths.root``
before invoking ``main()``. A ``sitecustomize.py`` file (added to the
repository) patches the read‑only ``paths.root`` property to make it
assignable during tests.
"""
import os
import sys
import logging
from pathlib import Path
from llmxive_toolkit import get_logger

# Initialize logger
log = get_logger(__name__)

# Pinned requirements (must match the repository's root ``requirements.txt``)
_REQUIREMENTS = """\
# Core scientific stack (already available in the base environment)
numpy
pandas
scipy
matplotlib
scikit-learn
statsmodels
seaborn
pytest
PyYAML
requests
jsonschema
psutil

# Additional dependencies required for this project
datasets
torch==2.2.0
opencv-python
tqdm
# The DeepGaze II model is fetched via torch.hub; no extra package needed.
"""

def _write_requirements_file() -> Path:
    """Write the pinned ``requirements.txt`` at the project root."""
    # Lazy import so that any monkey‑patching of ``paths.root`` takes effect
    from llmxive_toolkit import paths

    req_path = paths.root / "requirements.txt"
    req_path.parent.mkdir(parents=True, exist_ok=True)
    req_path.write_text(_REQUIREMENTS.strip() + "\n")
    log.info(f"Wrote pinned requirements to {req_path}")
    return req_path

def _create_directories() -> None:
    """
    Ensure that all required top‑level directories exist.
    The list follows the specification for T001.
    """
    # Lazy import to respect potential monkey‑patching of ``paths.root``
    from llmxive_toolkit import paths

    needed_dirs = [
        paths.code(),                     # code/
        paths.data("raw"),                # data/raw/
        paths.data("interim"),            # data/interim/
        paths.data("processed"),          # data/processed/
        paths.data("results"),            # data/results/
        paths.code("tests"),              # code/tests/
        paths.docs(),                     # docs/
    ]

    for d in needed_dirs:
        d.mkdir(parents=True, exist_ok=True)
        log.debug(f"Ensured directory exists: {d}")

def _print_directory_tree(root: Path = Path(".")) -> None:
    """
    Print a concise tree of the project layout.
    Only directories are shown to keep the output readable.
    """
    log.info("Project directory tree:")
    for dirpath, dirnames, _ in os.walk(root):
        # Sort for deterministic output
        dirnames.sort()
        depth = Path(dirpath).relative_to(root).parts
        indent = "│   " * (len(depth) - 1) + ("├── " if depth else "")
        print(f"{indent}{Path(dirpath).name}/")
        for d in dirnames:
            sub_indent = "│   " * len(depth) + "├── "
            print(f"{sub_indent}{d}/")

def main() -> int:
    """
    Entry point for the bootstrap script.

    Steps:
    1. Create required directories.
    2. Write the pinned ``requirements.txt`` at the project root.
    3. Print the directory tree as proof of successful setup.
    """
    log.info("Starting bootstrap process...")
    _create_directories()
    _write_requirements_file()
    # Use the root defined by ``paths.root``; this works even if the test
    # monkey‑patches it because the import is performed lazily inside the
    # helper functions.
    from llmxive_toolkit import paths
    _print_directory_tree(paths.root)
    log.info("Bootstrap completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
