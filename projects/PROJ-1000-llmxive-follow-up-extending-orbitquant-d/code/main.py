"""
code/main.py
Entry point for project initialization.

This script creates the required project skeleton under the `code/` directory,
adds `__init__.py` markers to make each sub‑package importable, and prints a
confirmation message. It is invoked by the quick‑start guide:

    python -m code.main --phase init

The script is deliberately lightweight and runs on CPU‑only environments.
"""
import argparse
import sys
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# List of sub‑directories that constitute the project skeleton.
# The quick‑start verification expects at least eight directories.
SUBDIRS = [
    "analysis",
    "models",
    "quantization",
    "evaluation",
    "utils",
    "runners",
    "validation",
    "data",
]

def create_package_dir(dir_path: Path) -> None:
    """
    Ensure a directory exists and contains an ``__init__.py`` file so that it
    is recognised as a Python package.

    Parameters
    ----------
    dir_path: Path
        The absolute path of the directory to create.
    """
    dir_path.mkdir(parents=True, exist_ok=True)
    init_file = dir_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()
    log.debug(f"Created package directory: {dir_path}")

def init_skeleton() -> None:
    """
    Create the required ``code/`` sub‑directories and ``tests/`` placeholder.
    """
    # Create sub‑packages under ``code/``.
    for sub in SUBDIRS:
        create_package_dir(paths.code(sub))

    # Ensure the top‑level ``tests/`` directory exists with a placeholder test.
    tests_dir = paths.tests("")
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "__init__.py").touch(exist_ok=True)

    placeholder_test = tests_dir / "test_placeholder.py"
    if not placeholder_test.exists():
        placeholder_test.write_text(
            "# placeholder test – always passes\\n"
            "def test_placeholder():\\n"
            "    assert True\\n"
        )
    log.debug("Created placeholder test in tests/")

def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Project skeleton initialisation for the OrbitQuant follow‑up."
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=["init"],
        help="Initialisation phase to run."
    )
    args = parser.parse_args(argv)

    if args.phase == "init":
        init_skeleton()
        print("Initialization complete")
        return 0

    # Should never reach here because argparse restricts choices.
    parser.error(f"Unsupported phase: {args.phase}")
    return 1

if __name__ == "__main__":
    sys.exit(main())
