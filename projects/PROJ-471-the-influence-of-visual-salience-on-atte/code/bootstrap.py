"""
Bootstrap script for the Visual Salience project.

This script creates the required project layout, writes a pinned
``requirements.txt`` file under ``code/`` and prints a directory tree
as proof of successful setup.
"""
import os
import sys
import logging
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# Initialize logger
log = get_logger(__name__)

# Pinned requirements (must match the root requirements.txt)
_REQUIREMENTS = """\
# Pinned dependencies for reproducibility
# Python version
python==3.11

# Core libraries
torch==2.2.0
torchvision==0.17.0
datasets==2.18.0
scikit-learn==1.4.0
statsmodels==0.14.2
opencv-python==4.9.0.80
ultralytics==8.2.2
detectron2==0.8
pandas==2.2.1
numpy==1.26.4
pingouin==0.5.4
psutil==5.9.8

# Formatting / linting tools
ruff==0.2.2
black==24.2.0
"""

def _write_requirements_file() -> Path:
    """Write the pinned requirements.txt under ``code/``."""
    req_path = paths.code("requirements.txt")
    req_path.parent.mkdir(parents=True, exist_ok=True)
    req_path.write_text(_REQUIREMENTS.strip() + "\n")
    log.info(f"Wrote pinned requirements to {req_path}")
    return req_path

def _create_directories() -> None:
    """
    Ensure that all required top‑level directories exist.
    The list follows the specification for T001.
    """
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

def main() -> None:
    """
    Entry point for the bootstrap script.

    Steps:
    1. Create required directories.
    2. Write the pinned ``requirements.txt``.
    3. Print the directory tree as proof of successful setup.
    """
    log.info("Starting bootstrap process...")
    _create_directories()
    _write_requirements_file()
    _print_directory_tree()
    log.info("Bootstrap completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
