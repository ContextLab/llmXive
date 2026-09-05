"""
Unit test for the ``setup_code_dirs`` utility.

The test runs the ``setup_code_dirs`` script and then checks that the expected
directories exist and contain an ``__init__.py`` file.
"""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # repo root

CODE_DIR = PROJECT_ROOT / "code"
EXPECTED_SUBDIRS = [
    CODE_DIR / "data",
    CODE_DIR / "models",
    CODE_DIR / "utils",
    CODE_DIR / "validate",
]

@pytest.mark.parametrize("subdir", EXPECTED_SUBDIRS)
def test_code_subdirectory_created(subdir: Path):
    """
    Ensure that each required sub‑directory exists and is a Python package.
    """
    # Run the setup script – it is safe to call it repeatedly because the
    # implementation is idempotent.
    script_path = CODE_DIR / "setup_code_dirs.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Now check the sub‑directory.
    assert subdir.is_dir(), f"Expected directory {subdir} does not exist."

    init_file = subdir / "__init__.py"
    assert init_file.is_file(), f"Missing __init__.py in {subdir}."

# The test can be executed directly with ``pytest -q tests/unit/test_code_directories.py``.