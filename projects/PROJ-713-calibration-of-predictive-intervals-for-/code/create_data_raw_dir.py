"""
Script to create the `data/raw/` directory in an idempotent fashion
and verify that it is writable.

This mirrors the verification scripts used for `code/` and `tests/`
directories (tasks T001a and T001b).
"""

from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def create_and_verify_data_raw_dir() -> None:
    """
    Create the `data/raw/` directory (if it does not already exist)
    and assert that the directory is writable.
    
    The function is idempotent: calling it multiple times has no adverse
    effect and will always leave the directory in a writable state.
    """
    # `paths.data("raw")` returns a Path object and ensures the directory exists.
    raw_dir: Path = paths.data("raw")
    log.debug(f"Ensured existence of raw data directory: {raw_dir}")

    # Verify write access by creating and deleting a temporary file.
    test_file = raw_dir / ".tmp_write_check"
    try:
        test_file.write_text("test")
        if test_file.read_text() != "test":
            raise IOError("Write verification failed: content mismatch.")
    finally:
        # Clean up the temporary file if it was created.
        if test_file.exists():
            test_file.unlink()

    log.info(f"`data/raw/` directory is present and writable at {raw_dir}")


if __name__ == "__main__":
    # When executed as a script, perform the creation and verification.
    create_and_verify_data_raw_dir()
