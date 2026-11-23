"""
Script to create required data directories and a CHECKSUMS manifest file.

This satisfies task T004 by ensuring that the following directories exist:
  - data/raw/
  - data/processed/
  - data/results/

It also creates an empty `data/CHECKSUMS` file if it does not already exist.
The script uses the project's `llmxive_toolkit.paths` helper to create
directories inside the project root and logs its actions via the
project's logger.
"""

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def ensure_dir(path):
    """Create a directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        log.info(f"Created directory: {path}")
    else:
        log.debug(f"Directory already exists: {path}")


def main():
    """Create data directories and an empty CHECKSUMS manifest."""
    # Define required directories
    raw_dir = paths.data("raw")
    processed_dir = paths.data("processed")
    results_dir = paths.data("results")

    # Ensure each directory exists
    for d in (raw_dir, processed_dir, results_dir):
        ensure_dir(d)

    # Create the CHECKSUMS manifest file if missing
    checksum_file = paths.data("CHECKSUMS")
    if not checksum_file.exists():
        checksum_file.touch()
        log.info(f"Created empty checksum manifest at {checksum_file}")
    else:
        log.debug(f"Checksum manifest already exists at {checksum_file}")


if __name__ == "__main__":
    main()