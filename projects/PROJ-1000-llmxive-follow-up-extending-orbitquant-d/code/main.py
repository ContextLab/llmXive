"""
Entry point for project initialization.

This script creates the required directory structure under the `code/`
package and prints a confirmation message. It is invoked by the quick‑start
command:

    python -m code.main --phase init

The script is deliberately simple: it validates the `--phase` argument,
creates the directories, and prints ``Initialization complete`` so that
the verification step can grep the expected phrase.
"""
import argparse
import sys
from pathlib import Path

from llmxive_toolkit import paths

# -------------------------------------------------------------------------
# Directory creation
# -------------------------------------------------------------------------
def _create_project_dirs() -> None:
    """
    Create all required project‑owned directories.

    The list includes the sub‑packages required by later tasks as well as
    common data/processed and figures folders. Each call is idempotent.
    """
    # Code sub‑packages
    subdirs = [
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

    for sub in subdirs:
        dir_path = paths.code(sub)
        dir_path.mkdir(parents=True, exist_ok=True)

    # Tests package
    paths.tests("").mkdir(parents=True, exist_ok=True)

    # Data folders
    paths.data("raw").mkdir(parents=True, exist_ok=True)
    paths.data("processed").mkdir(parents=True, exist_ok=True)

    # Figures folder
    paths.figures("").mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------------
# CLI handling
# -------------------------------------------------------------------------
def _parse_args(argv: list) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Project initialization script")
    parser.add_argument(
        "--phase",
        choices=["init"],
        required=True,
        help="Initialization phase to run",
    )
    # parse_known_args allows the quick‑start pipe to work without extra args
    args, _ = parser.parse_known_args(argv)
    return args

def main(argv: list | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])

    if args.phase == "init":
        _create_project_dirs()
        # The exact phrase is required by the verification grep
        print("Initialization complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())
