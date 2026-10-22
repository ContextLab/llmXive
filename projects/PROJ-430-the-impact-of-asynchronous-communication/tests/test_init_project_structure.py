"""
Unit test for ``init_project_structure.py``.

The test simply runs the script (importing its ``main`` function) and
asserts that the required directories now exist.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Path to the script relative to the repository root
SCRIPT_PATH = Path("code/init_project_structure.py")

@pytest.mark.timeout(60)
def test_directories_created(tmp_path, monkeypatch):
    """
    Run the script and verify that the expected directories exist.
    """
    # Ensure we run the script from the repository root
    repo_root = Path(__file__).resolve().parents[2]

    # Use subprocess to execute the script exactly as the run‑book would
    result = subprocess.run(
        [sys.executable, str(repo_root / SCRIPT_PATH)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    # The script must exit cleanly
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify each required directory exists
    project_root = repo_root / "projects" / "PROJ-430-the-impact-of-asynchronous-communication"
    for sub in ["code", "data", "tests", "docs", "config"]:
        assert (project_root / sub).is_dir(), f"Missing directory: {sub}"