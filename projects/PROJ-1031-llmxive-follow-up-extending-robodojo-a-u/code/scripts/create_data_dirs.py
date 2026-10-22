"""
Script to create the required data directory hierarchy for the project.

The verification step expects the following directories to exist under the
project root:
    data/raw/
    data/interim/
    data/processed/
    data/final/

This script uses the `paths` helper from `llmxive_toolkit` to create the
directories in a platform‑agnostic way. It is safe to run multiple times;
existing directories are left untouched.
"""

import sys
from llmxive_toolkit import paths, get_logger

# Set up a logger (optional, but useful for debugging)
log = get_logger(__name__)

def main() -> int:
    """Create the data sub‑folders and exit with a status code.

    Returns
    -------
    int
        0 on success, non‑zero on failure.
    """
    try:
        # The `paths.data` helper creates the parent directory if needed.
        # Passing a single component creates the folder directly under `data/`.
        for subfolder in ("raw", "interim", "processed", "final"):
            dir_path = paths.data(subfolder)
            dir_path.mkdir(parents=True, exist_ok=True)
            log.info("Created data directory: %s", dir_path)

        # Verify that all expected directories now exist.
        missing = [
            sub for sub in ("raw", "interim", "processed", "final")
            if not paths.data(sub).is_dir()
        ]
        if missing:
            log.error("Failed to create directories: %s", ", ".join(missing))
            return 1

        log.info("All required data directories are present.")
        return 0
    except Exception as e:
        log.exception("Unexpected error while creating data directories: %s", e)
        return 1

if __name__ == "__main__":
    sys.exit(main())
