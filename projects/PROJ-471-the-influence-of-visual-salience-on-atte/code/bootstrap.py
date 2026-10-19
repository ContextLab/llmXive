"""
Bootstrap script for the Visual Salience project (T001).

This script creates the required project layout — including the
top-level ``logs/`` directory required by the task — writes a pinned
``requirements.txt`` at the project root (mirrored into ``code/``)
and prints a directory tree as proof of successful setup.
"""
import os
import sys
import logging
from pathlib import Path
from llmxive_toolkit import get_logger, paths

# Initialize logger
log = get_logger(__name__)

# Pinned requirements: All dependencies required by the pipeline.
_REQUIREMENTS = """\
python==3.11
torch==2.2.0
statsmodels>=0.14.0
ultralytics>=8.0.0
detectron2>=0.7
pandas>=2.2.0
numpy>=1.26.0
scikit-image>=0.22.0
scikit-learn>=1.3.0
pingouin>=0.5.4
opencv-python>=4.8.0
datasets
huggingface_hub
"""

def _write_requirements_file() -> Path:
    """Write the pinned ``requirements.txt`` at the project root.

    A mirror copy is also placed inside ``code/`` so that both the
    documented ``pip install -r requirements.txt`` entry point and the
    historical ``code/requirements.txt`` reference resolve.
    """
    root_req = paths.root / "requirements.txt"
    root_req.parent.mkdir(parents=True, exist_ok=True)
    root_req.write_text(_REQUIREMENTS.strip() + "\n")
    log.info(f"Wrote pinned requirements to {root_req}")

    code_req = paths.code("requirements.txt")
    code_req.parent.mkdir(parents=True, exist_ok=True)
    code_req.write_text(_REQUIREMENTS.strip() + "\n")
    log.info(f"Wrote mirrored requirements to {code_req}")
    return root_req

def _create_directories() -> None:
    """
    Ensure that all required directories exist, including the
    top-level ``logs/`` directory required by the task description.
    """
    needed_dirs = [
        paths.code(),                     # code/
        paths.data("raw"),                # data/raw/
        paths.data("interim"),            # data/interim/
        paths.data("processed"),          # data/processed/
        paths.data("results"),            # data/results/
        paths.root / "logs",              # logs/  (top-level, required by T001)
        paths.code("tests"),              # code/tests/
        paths.docs(),                     # docs/
    ]

    for d in needed_dirs:
        d.mkdir(parents=True, exist_ok=True)
        log.debug(f"Ensured directory exists: {d}")

def _print_directory_tree(root: Path = None) -> None:
    """
    Print a concise tree of the project layout.
    Only directories are shown to keep the output readable.
    """
    if root is None:
        root = paths.root
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
