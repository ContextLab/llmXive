import sys
import logging
from pathlib import Path

from llmxive_toolkit import paths, get_logger
from create_project_structure import ensure_directories

log = get_logger(__name__)

def _verify_writable(directory: Path) -> bool:
    """
    Attempt to write and delete a temporary file in ``directory``.
    Returns True if successful, False otherwise.
    """
    try:
        test_file = directory / ".writetest"
        with open(test_file, "w") as f:
            f.write("test")
        test_file.unlink()
        return True
    except Exception as e:
        log.error(f"Directory not writable {directory}: {e}")
        return False

def main() -> None:
    """
    Entry point for project initialization.

    - Creates required directories.
    - Verifies each required directory exists and is writable.
    - Logs success or raises RuntimeError on failure.
    """
    # Ensure directories exist
    ensure_directories()

    required_dirs = [
        paths.code(),
        paths.data("raw"),
        paths.data("processed"),
        paths.results(),
        paths.tests("unit"),
        paths.tests("contract"),
    ]

    # Verify existence
    missing = [p for p in required_dirs if not p.exists()]
    if missing:
        raise RuntimeError(f"Missing required directories: {missing}")

    # Verify writability
    not_writable = [p for p in required_dirs if not _verify_writable(p)]
    if not_writable:
        raise RuntimeError(f"Directories not writable: {not_writable}")

    log.info("Project initialization successful – all required directories exist and are writable.")

if __name__ == "__main__":
    main()
