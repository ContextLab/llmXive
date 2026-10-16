"""
Bootstrap script for the Visual Salience project.

This script creates the required project layout, writes a pinned
``requirements.txt`` file at the project root and prints a directory
tree as proof of successful setup.
"""
import os
import sys
import logging
from pathlib import Path
from llmxive_toolkit import get_logger, paths

# Initialize logger
log = get_logger(__name__)

# Pinned requirements: Only those NOT provided by the platform environment.
# Based on plan.md and existing requirements.txt.
_REQUIREMENTS = """\
datasets
torch==2.2.0
opencv-python
huggingface_hub
ultralytics
detectron2
pingouin
"""

def _write_requirements_file() -> Path:
    """Write the pinned ``requirements.txt`` at the project root."""
    req_path = paths.root / "requirements.txt"
    req_path.parent.mkdir(parents=True, exist_ok=True)
    req_path.write_text(_REQUIREMENTS.strip() + "\n")
    log.info(f"Wrote pinned requirements to {req_path}")
    return req_path

def _create_directories() -> None:
    """
    Ensure that all required top‑level directories exist.
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

def _print_directory_tree(root: Path = paths.root) -> None:
    """
    Print a concise tree of the project layout.
    Only directories are shown to keep the output readable.
    """
    print("\nProject directory tree:")
    for dirpath, dirnames, _ in os.walk(root):
        # Sort for deterministic output
        dirnames.sort()
        try:
            rel_path = Path(dirpath).relative_to(root)
        except ValueError:
            continue
        
        depth = rel_path.parts
        indent = "│   " * (len(depth) - 1) + ("├── " if depth else "")
        name = Path(dirpath).name if depth else "."
        print(f"{indent}{name}/")
        
        for d in dirnames:
            sub_indent = "│   " * len(depth) + "├── "
            print(f"{sub_indent}{d}/")

def main() -> int:
    """
    Entry point for the bootstrap script.
    """
    log.info("Starting bootstrap process...")
    try:
        _create_directories()
        _write_requirements_file()
        _print_directory_tree()
        log.info("Bootstrap completed successfully.")
        return 0
    except Exception as e:
        log.exception(f"Bootstrap failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
