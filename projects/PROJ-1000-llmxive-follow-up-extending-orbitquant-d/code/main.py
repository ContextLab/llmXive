"""
Entry point for project initialization.

Usage:
    python -m code.main --phase init
"""
import argparse
import sys

from llmxive_toolkit import paths, get_logger

# Initialize logger (optional, can be omitted if not needed)
log = get_logger(__name__)

def _create_subdirectories():
    """
    Create all required sub‑directories under the `code/` package
    and the `tests/` directory. Uses `llmxive_toolkit.paths` helpers
    to ensure the directories are created inside the project root.
    """
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
        # `paths.code` creates the directory if it does not exist.
        dir_path = paths.code(sub)
        log.info(f"Created code subdirectory: {dir_path}")

    # Ensure the top‑level `tests/` directory exists.
    tests_path = paths.tests("")
    log.info(f"Created tests directory: {tests_path}")

def main(argv=None):
    parser = argparse.ArgumentParser(description="Project entry point.")
    parser.add_argument(
        "--phase",
        type=str,
        required=True,
        help="Initialization phase to run (currently only 'init' is supported).",
    )
    args = parser.parse_args(argv)

    if args.phase == "init":
        _create_subdirectories()
        # Print the exact phrase expected by the verification step.
        print("Initialization complete")
        return 0
    else:
        parser.error(f"Unsupported phase: {args.phase}")

if __name__ == "__main__":
    sys.exit(main())
