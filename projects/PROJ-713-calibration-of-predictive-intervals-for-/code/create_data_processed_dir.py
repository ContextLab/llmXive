"""
Script to create and verify the existence and writability of the
``data/processed`` directory.

This mirrors the behavior of the existing ``create_code_dir.py`` and
``create_data_raw_dir.py`` utilities and is used by the verification
step for task T001d.
"""

import os
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def create_and_verify_data_processed_dir() -> Path:
    """
    Create the ``data/processed`` directory (idempotent) and assert that it
    is writable.

    Returns
    -------
    Path
        The absolute path to the created ``data/processed`` directory.
    """
    # Resolve the target directory using the toolkit helper.
    processed_dir: Path = paths.data("processed")
    # Create the directory (idempotent).
    processed_dir.mkdir(parents=True, exist_ok=True)
    log.debug(f"Ensured directory exists: {processed_dir}")

    # Verify write permission on the directory.
    if not os.access(str(processed_dir), os.W_OK):
        raise PermissionError(f"Directory is not writable: {processed_dir}")

    log.info(f"Directory verified as writable: {processed_dir}")
    return processed_dir

if __name__ == "__main__":
    # When run as a script, simply execute the creation routine.
    try:
        create_and_verify_data_processed_dir()
    except Exception as exc:
        log.error(f"Failed to create/verify data/processed directory: {exc}")
        raise
