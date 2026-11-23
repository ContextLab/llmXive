"""
Initialise the project directory layout and generate a directory listing.

This script creates the required project sub‑directories under the project
root and writes a listing of all directories (including the newly created
ones) to ``results/dir_listing.txt`` using the ``find`` command.

The script is intended to be run as part of the initialisation step
(e.g. ``python code/init_project.py``).  It exits with status 0 on success
and non‑zero on failure.
"""
import subprocess
import sys
from pathlib import Path

# llmxive_toolkit helpers – they create parent directories when used.
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Directories that must exist (relative to the project root)
REQUIRED_DIRS = [
    Path("data/raw"),
    Path("data/processed"),
    Path("data/embeddings"),
    Path("data/clustering"),
    Path("data/metrics"),
    Path("data/results"),
    Path("figures"),
    Path("code"),
    Path("code/tests"),
    Path("paper"),
]

def _create_directories() -> None:
    """Create all required directories (parents are created as needed)."""
    for d in REQUIRED_DIRS:
        # ``Path.mkdir`` with ``parents=True`` works even if the directory
        # already exists; ``exist_ok=True`` suppresses errors.
        d_path = Path(d)
        d_path.mkdir(parents=True, exist_ok=True)
        log.info(f"Created directory: {d_path}")

def _write_listing_via_find() -> None:
    """
    Run ``find`` to collect all directories under the top‑level
    folders and write the result to ``results/dir_listing.txt``.
    """
    # Ensure the ``results`` directory exists before writing the file.
    results_dir = paths.results()
    results_dir.mkdir(parents=True, exist_ok=True)

    # ``find`` arguments – we search the top‑level folders that contain
    # the directories we care about.
    find_cmd = [
        "find",
        "data",
        "code",
        "results",
        "figures",
        "paper",
        "-type",
        "d",
    ]

    try:
        log.info(f"Running find command: {' '.join(find_cmd)}")
        completed = subprocess.run(
            find_cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        log.error(f"Find command failed: {e.stderr}")
        raise

    listing_path = results_dir / "dir_listing.txt"
    listing_path.write_text(completed.stdout)
    log.info(f"Directory listing written to {listing_path}")

def main() -> int:
    """Entry point for the initialisation script."""
    try:
        _create_directories()
        _write_listing_via_find()
    except Exception as exc:  # pragma: no cover – any error is fatal
        log.error(f"Initialisation failed: {exc}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
