"""
Project Initialization Script
------------------------------

This script ensures that the required project directory structure exists and is writable.
It is intended to satisfy task T001a, which verifies that the following directories are present:

- projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/
- data/raw/
- data/processed/
- results/
- tests/unit/
- tests/contract/

The implementation reuses the existing ``ensure_directories`` helper from
``code/create_project_structure.py`` to perform the actual creation.
After invoking the helper, the script performs a quick sanity‑check by attempting
to create and delete a temporary file in each directory, guaranteeing writability.
"""

import sys
import logging
from pathlib import Path
from create_project_structure import ensure_directories

# Configure a simple logger; the project's ``config.setup_logging`` is not
# imported here to avoid circular imports during early bootstrap.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

# List of directories that must exist relative to the project root.
REQUIRED_DIRS = [
    Path("code"),
    Path("data/raw"),
    Path("data/processed"),
    Path("results"),
    Path("tests/unit"),
    Path("tests/contract"),
]

def _verify_writable(directory: Path) -> bool:
    """Attempt to write and delete a temporary file in ``directory``."""
    try:
        test_file = directory / ".init_test.tmp"
        test_file.write_text("init")
        test_file.unlink()
        return True
    except Exception as exc:
        log.error(f"Directory not writable: {directory} – {exc}")
        return False

def main() -> None:
    """Entry point for the initialization script."""
    log.info("Running project initialization…")
    ensure_directories()
    all_ok = True
    for d in REQUIRED_DIRS:
        if not d.is_dir():
            log.error(f"Missing required directory: {d}")
            all_ok = False
            continue
        if not _verify_writable(d):
            all_ok = False
    if not all_ok:
        log.error("Project initialization failed – see errors above.")
        sys.exit(1)
    log.info("All required directories exist and are writable.")

if __name__ == "__main__":
    main()
