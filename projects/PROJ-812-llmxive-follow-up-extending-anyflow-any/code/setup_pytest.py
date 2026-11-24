"""
Script to set up pytest configuration and ensure the required test
directory structure exists for the project.

This script creates:
  - tests/unit/
  - tests/integration/
and adds an empty ``__init__.py`` to each to make them importable
packages. It also creates a ``pytest.ini`` file at the project root
if it does not already exist.

The script is idempotent: running it multiple times will not overwrite
existing files.
"""

import sys
from pathlib import Path

# llmxive_toolkit provides a logger utility; use it for consistent logging
from llmxive_toolkit import get_logger

LOG = get_logger(__name__)

def _ensure_test_dir(sub_dir: str) -> None:
    """Create a test sub‑directory (unit or integration) with an __init__.py."""
    test_path = Path("tests") / sub_dir
    test_path.mkdir(parents=True, exist_ok=True)
    init_file = test_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()
    LOG.info("Ensured test directory %s", test_path)

def _ensure_pytest_ini() -> None:
    """Create a minimal pytest.ini at the repository root if missing."""
    ini_path = Path("pytest.ini")
    if ini_path.exists():
        LOG.info("pytest.ini already exists at %s", ini_path)
        return

    content = (
        "[pytest]\n"
        "# Discover test files matching the typical patterns\n"
        "python_files = test_*.py *_test.py\n"
        "# Show extra test summary info for passed, skipped, and xfailed tests\n"
        "addopts = -ra -v\n"
        "# Enable markers (if needed in future)\n"
        "markers =\n"
        "    unit: unit tests\n"
        "    integration: integration tests\n"
    )
    ini_path.write_text(content)
    LOG.info("Created pytest.ini at %s", ini_path)

def main() -> int:
    """Entry point for the setup script."""
    LOG.info("Starting pytest configuration and directory setup")
    try:
        for sub in ("unit", "integration"):
            _ensure_test_dir(sub)
        _ensure_pytest_ini()
    except Exception as exc:  # pragma: no cover
        LOG.error("Failed to set up pytest environment: %s", exc)
        return 1
    LOG.info("Pytest setup completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())