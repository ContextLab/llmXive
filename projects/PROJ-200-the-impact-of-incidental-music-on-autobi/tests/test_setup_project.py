"""
Integration test for ``code/setup_project.py``.
"""
import subprocess
import sys
from pathlib import Path
import pytest
from config import get_project_root

@pytest.mark.timeout(30)
def test_setup_project_creates_directories(monkeypatch):
    """
    Run ``python code/setup_project.py`` and assert that the required
    directories are present after execution.
    """
    project_root = get_project_root()
    monkeypatch.chdir(project_root)

    result = subprocess.run(
        [sys.executable, "code/setup_project.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    expected_dirs = [
        "data/raw",
        "data/processed",
        "data/final",
        "data/final/plots",
        "code",
        "tests",
        "contracts",
        "specs",
        "logs",
    ]

    for rel_dir in expected_dirs:
        path = project_root / rel_dir
        assert path.is_dir(), f"Expected directory missing: {rel_dir}"