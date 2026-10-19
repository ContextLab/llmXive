"""
Script to create the required project directory tree and generate a
plain‑text directory listing at ``results/dir_listing.txt``.

The directories created are:
  data/raw/
  data/processed/
  data/embeddings/
  data/clustering/
  data/metrics/
  data/results/
  figures/
  results/
  code/
  code/tests/
  paper/
  .github/workflows/

After creation, the script runs the equivalent of:
    find data code results figures paper .github -type d > results/dir_listing.txt

The script is idempotent – running it again will not raise errors.
"""

import subprocess
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# Initialise logger (INFO level, console + file handled by the toolkit)
log = get_logger(__name__)

# List of directories (relative to the project root) that must exist.
REQUIRED_DIRS = [
    Path("data/raw"),
    Path("data/processed"),
    Path("data/embeddings"),
    Path("data/clustering"),
    Path("data/metrics"),
    Path("data/results"),
    Path("figures"),
    Path("results"),
    Path("code"),
    Path("code/tests"),
    Path("paper"),
    Path(".github/workflows"),
]


def _create_directories() -> None:
    """Create all required directories (parents are created as needed)."""
    for rel_dir in REQUIRED_DIRS:
        abs_dir = paths.root / rel_dir
        abs_dir.mkdir(parents=True, exist_ok=True)
        log.info(f"Ensured directory exists: {abs_dir}")


def _write_listing_via_find() -> None:
    """
    Run ``find`` to collect all directories under the top‑level folders and
    write the result to ``results/dir_listing.txt``.
    """
    # Ensure the results directory exists
    listing_path = paths.results("dir_listing.txt")
    listing_path.parent.mkdir(parents=True, exist_ok=True)

    # ``find`` command arguments
    find_cmd = [
        "find",
        "data",
        "code",
        "results",
        "figures",
        "paper",
        ".github",
        "-type",
        "d",
    ]

    log.info(f"Running find command to generate directory listing: {' '.join(find_cmd)}")
    completed = subprocess.run(
        find_cmd,
        cwd=paths.root,
        capture_output=True,
        text=True,
        check=True,
    )

    # Write the stdout (the list of directories) to the target file
    listing_path.write_text(completed.stdout)
    log.info(f"Directory listing written to {listing_path}")


def main() -> None:
    """Entry point – create directories then write the listing."""
    _create_directories()
    _write_listing_via_find()


if __name__ == "__main__":
    main()