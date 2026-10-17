"""
Setup script for T001: Create required project directory hierarchy
and verify that each directory is writable.

This script is idempotent – it can be run multiple times without
affecting existing contents. It creates the following sub‑directories
under the project root (the directory containing this script's
``code/`` folder):

  - code/
  - tests/
  - data/
  - notebooks/
  - state/
  - data/raw/
  - data/processed/
  - data/events/
  - data/taxonomy/

After creation, the script attempts to write and delete a temporary
file in each directory to confirm writability. If any check fails,
the script exits with a non‑zero status and logs the error.
"""

import sys
import tempfile
from pathlib import Path

# llmxive_toolkit provides convenient path helpers and a logger
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def ensure_directories(root: Path, dirs: list[Path]) -> None:
    """Create each directory if it does not exist."""
    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
            log.info(f"Ensured directory exists: {d}")
        except Exception as exc:
            log.error(f"Failed to create directory {d}: {exc}")
            raise

def verify_writable(dirs: list[Path]) -> None:
    """Attempt to write and delete a temporary file in each directory."""
    for d in dirs:
        try:
            # Use NamedTemporaryFile with delete=False so we can control removal
            with tempfile.NamedTemporaryFile(dir=d, delete=False) as tmp:
                tmp_path = Path(tmp.name)
            # Close file already done by context manager; now delete it
            tmp_path.unlink()
            log.info(f"Writability verified for: {d}")
        except Exception as exc:
            log.error(f"Directory not writable: {d} – {exc}")
            raise

def main() -> int:
    # Root of the repository (project root)
    project_root = paths.root

    # Define required sub‑directories relative to the project root
    required_dirs = [
        project_root / "code",
        project_root / "tests",
        project_root / "data",
        project_root / "notebooks",
        project_root / "state",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "events",
        project_root / "data" / "taxonomy",
    ]

    try:
        log.info("Starting T001: directory creation and verification")
        ensure_directories(project_root, required_dirs)
        verify_writable(required_dirs)
        log.info("All required directories are present and writable.")
    except Exception:
        # Propagate the error so the script exits with a non‑zero code
        log.error("Directory setup failed; aborting.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())