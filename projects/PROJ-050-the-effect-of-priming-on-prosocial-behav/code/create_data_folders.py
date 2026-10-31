"""
Script to create the project's data folders.

This script is the public entry‑point used by the pipeline and the test
suite. It delegates the actual creation work to
``code.utils.directory_setup.create_directory_structure`` and returns a
list of the primary Path objects for convenience.
"""

import sys
from pathlib import Path

from llmxive_toolkit import get_logger
from code.utils.directory_setup import create_directory_structure, PROJECT_ROOT

def create_folders() -> list[Path]:
    """
    Create the required data folders and return their Path objects.

    Returns
    -------
    list[Path]
        Paths for ``data/raw``, ``data/processed``, ``data/validation``,
        and the legacy top‑level ``results`` directory.
    """
    logger = get_logger(__name__)
    if not create_directory_structure(logger):
        logger.error("Directory creation failed")
        sys.exit(1)

    # Use the llmxive ``paths`` helpers for consistency with the rest of
    # the codebase. They automatically create the parent directories.
    from llmxive_toolkit import paths  # local import to avoid circularity

    raw_path = paths.data("raw")
    processed_path = paths.data("processed")
    validation_path = paths.data("validation")
    results_path = paths.results()  # legacy top‑level folder

    return [raw_path, processed_path, validation_path, results_path]

def main() -> None:
    """
    CLI entry point – simply invoke ``create_folders``.
    """
    create_folders()

if __name__ == "__main__":
    main()