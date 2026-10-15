"""
Integration test for ``code/setup_project.py``.

The test runs the script (via ``subprocess``) and then verifies that the
expected directories exist.  This ensures that the quick‑start command
documented in ``quickstart.md`` works out‑of‑the‑box.
"""
import subprocess
import sys
from pathlib import Path

import pytest

# Import the project's configuration helpers to locate the root.
from config import get_project_root

@pytest.mark.timeout(30)
def test_setup_project_creates_directories(tmp_path, monkeypatch):
    """
    Run ``python code/setup_project.py`` and assert that the required
    directories are present after execution.
    """
    # Ensure the script runs from the repository root.
    project_root = get_project_root()
    monkeypatch.chdir(project_root)

    # Execute the script.
    result = subprocess.run(
        [sys.executable, "code/setup_project.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Expected directories relative to the project root.
    expected_dirs = [
        "data/raw",
        "data/processed",
        "data/final",
        "data/final/plots",
        "code",
        "tests",
        "contracts",
        "specs",
    ]

    for rel_dir in expected_dirs:
        path = project_root / rel_dir
        assert path.is_dir(), f"Expected directory missing: {rel_dir}"
