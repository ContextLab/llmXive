"""
Setup script to create the required project directory structure.

This script is idempotent and can be run multiple times without error.
It creates the following directories under the project root:

- code/
- data/raw/
- data/processed/
- data/outputs/figures/
- tests/unit/
- tests/integration/
- tests/contract/
"""

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _create_dir(path):
    """Create a directory (including parents) if it does not exist."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        log.debug(f"Created directory: {path}")
    except Exception as e:
        log.error(f"Failed to create directory {path}: {e}")
        raise

def main() -> int:
    """
    Entry point for the directory-creation script.

    Returns:
        int: Exit status (0 for success, non‑zero for failure).
    """
    # List of directories to ensure exist.
    dirs_to_create = [
        paths.code(),                                 # code/
        paths.data("raw"),                            # data/raw/
        paths.data("processed"),                      # data/processed/
        paths.data("outputs", "figures"),             # data/outputs/figures/
        paths.tests("unit"),                          # tests/unit/
        paths.tests("integration"),                   # tests/integration/
        paths.tests("contract"),                      # tests/contract/
    ]

    for dir_path in dirs_to_create:
        _create_dir(dir_path)

    log.info("All required directories have been created successfully.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())