"""
Unit test for the layout‑creation script.

The test runs the script in a temporary directory and checks that the
expected folders and ``__init__.py`` files are present after execution.
"""

import subprocess
import sys
from pathlib import Path
import pytest

@pytest.fixture
def temp_project(tmp_path, monkeypatch):
    """
    Create a temporary copy of the repository root for the test.
    """
    # Change cwd to the temporary directory
    monkeypatch.chdir(tmp_path)
    # Copy the script into the temp directory
    src_script = Path(__file__).parents[2] / "code" / "layout" / "create_layout.py"
    dest_dir = tmp_path / "code" / "layout"
    dest_dir.mkdir(parents=True)
    dest_script = dest_dir / "create_layout.py"
    dest_script.write_text(src_script.read_text())
    return tmp_path

def test_create_layout_runs_successfully(temp_project):
    script_path = Path("code/layout/create_layout.py")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0
    # Verify directories
    for sub in ["raw", "processed", "results", "metadata", "figures"]:
        assert (Path("data") / sub).is_dir()
    # Verify __init__ files
    for pkg in ["code", "code/config", "code/utils"]:
        init_file = Path(pkg) / "__init__.py"
        assert init_file.is_file()
    # Simple sanity check on output
    assert "Project layout created/verified successfully." in result.stdout.strip()