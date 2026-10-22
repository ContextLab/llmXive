"""
Main entry point for the project skeleton initialization.

This script creates the required sub‑directories under the ``code/`` package,
adds ``__init__.py`` markers so that they are recognised as Python packages,
and prints a confirmation message.

The quick‑start guide (``specs/001‑llmxive‑followup‑extending‑orbitquant‑d/quickstart.md``)
expects the command::

    python -m code.main --phase init

to output the line ``Initialization complete``.
"""
import argparse
import sys
from pathlib import Path
from llmxive_toolkit import paths

def create_subdirs(base_path: Path, subdirs):
    """
    Create sub‑directories under ``base_path`` and ensure each contains an
    ``__init__.py`` file so that it is a proper Python package.
    """
    for sub in subdirs:
        dir_path = base_path / sub
        dir_path.mkdir(parents=True, exist_ok=True)
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()

def main():
    parser = argparse.ArgumentParser(description="Project skeleton initializer")
    parser.add_argument(
        "--phase",
        required=True,
        choices=["init"],
        help="Initialization phase to run (currently only 'init' is supported)."
    )
    args = parser.parse_args()

    if args.phase == "init":
        # Root of the ``code`` package
        code_root = Path(__file__).resolve().parent

        # List of required sub‑directories (as specified in the quick‑start)
        required_subdirs = [
            "analysis",
            "models",
            "quantization",
            "evaluation",
            "utils",
            "data",
            "runners",
            "validation",
            "security",
        ]

        create_subdirs(code_root, required_subdirs)

        # Ensure the top‑level ``tests`` directory exists with an ``__init__`` file
        tests_dir = paths.root / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        init_test = tests_dir / "__init__.py"
        if not init_test.exists():
            init_test.touch()

        print("Initialization complete")
        sys.exit(0)
    else:
        parser.error(f"Unsupported phase: {args.phase}")

if __name__ == "__main__":
    main()
