"""
create_project_tree.py

Script to initialise the project directory layout and generate a
verifiable listing of the created directories.

The required directories are:
  - data/raw/
  - data/processed/
  - data/embeddings/
  - data/clustering/
  - data/metrics/
  - data/results/
  - figures/
  - code/
  - code/tests/
  - paper/

After creation, the script runs a ``find`` command to collect all
directories under the top‑level folders and writes the result to
``results/dir_listing.txt``.
"""
import subprocess
from pathlib import Path

from llmxive_toolkit import get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _create_directories() -> None:
    """
    Create all required project directories (parents are created as needed).
    """
    required_dirs = [
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

    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)
        log.info(f"Created directory: {d}")

def _write_listing_via_find() -> None:
    """
    Run ``find`` to collect all directories under the specified top‑level
    folders and write the result to ``results/dir_listing.txt``.
    """
    # Ensure the results folder exists
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / "dir_listing.txt"

    # The ``find`` command works on Unix‑like environments (the runner uses Linux)
    cmd = [
        "find",
        "data",
        "code",
        "results",
        "figures",
        "paper",
        "-type",
        "d",
    ]

    log.info(f"Running command: {' '.join(cmd)}")
    with output_file.open("w", encoding="utf-8") as f:
        subprocess.run(cmd, stdout=f, check=True)

    log.info(f"Directory listing written to {output_file}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Initialise the project layout and generate the directory listing.
    """
    _create_directories()
    _write_listing_via_find()
    log.info("Project initialisation complete.")

if __name__ == "__main__":
    # When executed as a script, run the main routine.
    main()
