"""
Bootstrap script for the Visual Salience project (T001).

This script establishes the project layout, generates the pinned 
requirements.txt, and documents the runnable entry point in quickstart.md.
It now accepts a ``--root <dir>`` argument and patches ``llmxive_toolkit.paths.root``
for the duration of the run, ensuring that all generated files and directories
are created under the supplied root (which satisfies the unit test that monkey‑patches
``paths.root``).
"""
import argparse
import os
import sys
import logging
from pathlib import Path
from llmxive_toolkit import get_logger, paths

# Initialize logger
log = get_logger(__name__)

# Pinned requirements as explicitly defined in T001
_REQUIREMENTS = [
    "torch==2.2.0",
    "statsmodels>=0.14.0",
    "ultralytics>=8.0.0",
    "detectron2>=0.7",
    "pandas>=2.2.0",
    "numpy>=1.26.0",
    "scikit-image>=0.22.0",
    "scikit-learn>=1.3.0",
    "pingouin>=0.5.4",
    "opencv-python>=4.8.0",
]

def _write_requirements_file() -> Path:
    """Write the pinned requirements.txt at the project root."""
    req_text = "\n".join(_REQUIREMENTS) + "\n"
    root_req = paths.root / "requirements.txt"
    root_req.parent.mkdir(parents=True, exist_ok=True)
    root_req.write_text(req_text)
    log.info(f"Wrote pinned requirements to {root_req}")

    # Mirror to code/requirements.txt for legacy compatibility
    code_req = paths.code("requirements.txt")
    code_req.parent.mkdir(parents=True, exist_ok=True)
    code_req.write_text(req_text)
    log.info(f"Wrote mirrored requirements to {code_req}")
    return root_req

def _create_directories() -> None:
    """
    Ensure the standard directory tree exists.
    Required: code/, data/raw/, data/interim/, data/processed/, logs/
    """
    needed_dirs = [
        paths.code(),                     # code/
        paths.data("raw"),                # data/raw/
        paths.data("interim"),            # data/interim/
        paths.data("processed"),          # data/processed/
        paths.root / "logs",              # logs/ (top‑level)
        paths.code("tests"),              # code/tests/
        paths.docs(),                     # docs/
    ]

    for d in needed_dirs:
        d.mkdir(parents=True, exist_ok=True)
        log.debug(f"Ensured directory exists: {d}")

def _update_quickstart() -> None:
    """
    Document the runnable entry point in quickstart.md.
    """
    qs_path = paths.root / "quickstart.md"
    content = (
        "# Quickstart\\n\\n"
        "## Installation\\n"
        "```bash\\n"
        "pip install -r requirements.txt\\n"
        "```\\n\\n"
        "## Run Entry Point\\n"
        "To run a smoke test of the pipeline, use:\\n"
        "```bash\\n"
        "python -m code.main --stage smoke\\n"
        "```\\n"
    )
    qs_path.write_text(content)
    log.info(f"Updated quickstart.md at {qs_path}")

def _print_directory_tree(root: Path = None) -> None:
    """Print the directory tree for verification."""
    if root is None:
        root = paths.root
    print("\\nProject directory tree:")
    for dirpath, dirnames, _ in os.walk(root):
        dirnames.sort()
        try:
            rel_path = Path(dirpath).relative_to(root)
        except ValueError:
            continue
        depth = rel_path.parts
        indent = "│   " * (len(depth) - 1) + ("├── " if depth else "")
        name = Path(dirpath).name if depth else "."
        print(f"{indent}{name}/")

def _patch_paths_root(new_root: Path) -> None:
    """
    Patch ``llmxive_toolkit.paths.root`` so that all helper functions
    (paths.code, paths.data, etc.) resolve relative to ``new_root``.
    This is required for the unit test which monkey‑patches ``paths.root``.
    """
    paths.root = new_root
    log.debug(f"Patched paths.root to {new_root}")

def main() -> int:
    """Entry point for the bootstrap script."""
    parser = argparse.ArgumentParser(
        description="Bootstrap the project directory layout."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Root directory for the project layout (default: current paths.root).",
    )
    # Use parse_known_args to ignore any extraneous arguments injected by pytest or other callers.
    args, _ = parser.parse_known_args()

    # If a root is supplied, patch the toolkit's root variable.
    if args.root is not None:
        _patch_paths_root(args.root.resolve())

    log.info("Starting bootstrap process...")
    try:
        _create_directories()
        _write_requirements_file()
        _update_quickstart()
        _print_directory_tree()
        log.info("Bootstrap completed successfully.")
        return 0
    except Exception as e:
        log.exception(f"Bootstrap failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())