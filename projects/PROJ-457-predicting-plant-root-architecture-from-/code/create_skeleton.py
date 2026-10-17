"""
create_skeleton.py
------------------
Script to create the required project directory skeleton and write a
`directory_structure.txt` file that lists the six required directories.
This satisfies task T001.
"""

import sys
from pathlib import Path

# llmxive_toolkit provides helpers for project‑relative paths
from llmxive_toolkit import paths, get_logger


def _ensure_directories() -> None:
    """
    Create the six required directories if they do not already exist.
    """
    # Required directories (relative to project root)
    required_dirs = [
        paths.code(),
        paths.tests(),
        paths.data("raw"),
        paths.data("processed"),
        paths.artifacts(),
        paths.artifacts("logs"),
    ]

    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)


def _write_directory_structure_file() -> None:
    """
    Write `directory_structure.txt` at the project root, listing each
    required directory on its own line.
    """
    root = paths.root
    output_path = root / "directory_structure.txt"

    # Relative paths for readability
    rel_paths = [
        "code/",
        "tests/",
        "data/raw/",
        "data/processed/",
        "artifacts/",
        "artifacts/logs/",
    ]

    with output_path.open("w", encoding="utf-8") as f:
        for line in rel_paths:
            f.write(line + "\n")


def main() -> int:
    """
    Entry point: create directories, write the listing, and log progress.
    Returns exit code 0 on success.
    """
    logger = get_logger(__name__)
    logger.info("Creating project directory skeleton for T001.")

    try:
        _ensure_directories()
        _write_directory_structure_file()
        logger.info(
            "Directory skeleton created and recorded in directory_structure.txt."
        )
        return 0
    except Exception as exc:
        logger.error("Failed to create directory skeleton: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
