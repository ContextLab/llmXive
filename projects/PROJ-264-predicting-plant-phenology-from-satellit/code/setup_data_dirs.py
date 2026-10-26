"""
Script to create required data directory structure for the project.

This script is part of task T001c and ensures that the following directories
exist under the project root:

  data/raw/
  data/processed/

It uses the `llmxive_toolkit.paths` helper which automatically creates any
missing parent directories.
"""

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def create_directory(path):
    """
    Ensure a directory exists.

    Parameters
    ----------
    path : pathlib.Path
        The directory path to create.
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        log.info(f"Created directory: {path}")
    else:
        log.debug(f"Directory already exists: {path}")

def main() -> int:
    """
    Entry point for the script.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure)
    """
    try:
        # Create the required data directories
        raw_dir = paths.data("raw")
        processed_dir = paths.data("processed")

        create_directory(raw_dir)
        create_directory(processed_dir)

        # Success
        return 0
    except Exception as e:
        log.error(f"Failed to create data directories: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
