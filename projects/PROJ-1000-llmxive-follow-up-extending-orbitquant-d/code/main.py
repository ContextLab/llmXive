"""
Main entry point for the llmXive follow‑up project.

Provides a simple command‑line interface with a single ``--phase`` argument.
The ``init`` phase creates the required project skeleton under the ``code/``
package (sub‑directories and ``__init__.py`` markers) and prints a
confirmation message.

The script is safe to run multiple times; existing directories and files
are left untouched.
"""
import argparse
import sys
from pathlib import Path
from llmxive_toolkit import paths, get_logger

# Configure a module‑level logger (optional)
log = get_logger(__name__)

# List of sub‑directories that must exist under ``code/``
SUBDIRS = [
    "analysis",
    "models",
    "quantization",
    "evaluation",
    "utils",
    "runners",
    "data",
    "validation",
]


def _ensure_package_dir(dir_path: Path) -> None:
    """
    Ensure that ``dir_path`` exists and contains an ``__init__.py`` file
    so that it is recognised as a Python package.
    """
    dir_path.mkdir(parents=True, exist_ok=True)
    init_file = dir_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        log.info(f"Created package marker: {init_file}")


def init_skeleton() -> None:
    """
    Create the required directory hierarchy under ``code/``.
    """
    for sub in SUBDIRS:
        pkg_path = paths.code(sub)
        _ensure_package_dir(pkg_path)
    # Also ensure the top‑level ``code`` package has an ``__init__.py``
    root_init = paths.code("__init__.py")
    if not root_init.exists():
        root_init.touch()
        log.info(f"Created top‑level package marker: {root_init}")

    # Create a placeholder ``tests`` package if it does not already exist
    tests_path = paths.tests("")
    tests_path.mkdir(parents=True, exist_ok=True)
    tests_init = tests_path / "__init__.py"
    if not tests_init.exists():
        tests_init.touch()
        log.info(f"Created tests package marker: {tests_init}")

    print("Initialization complete")


def parse_args(argv: list | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Project skeleton initialisation for llmXive follow‑up."
    )
    parser.add_argument(
        "--phase",
        type=str,
        required=True,
        help="Execution phase (currently only 'init' is supported).",
    )
    return parser.parse_args(argv)


def main(argv: list | None = None) -> int:
    args = parse_args(argv)
    if args.phase == "init":
        init_skeleton()
    else:
        log.error(f"Unsupported phase: {args.phase}")
        print(f"Error: unsupported phase '{args.phase}'", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
