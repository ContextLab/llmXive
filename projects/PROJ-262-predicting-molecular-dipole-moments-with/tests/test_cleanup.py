"""Test that the cleanup script runs without errors."""
from __future__ import annotations

import subprocess
import sys
import pathlib

def test_clean_up_script_runs_successfully() -> None:
    """Execute `code/clean_up.py` and assert a zero exit code."""
    script_path = pathlib.Path(__file__).resolve().parents[1] / "code" / "clean_up.py"
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    # Debug output in case of failure
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr, file=sys.stderr)
    assert result.returncode == 0, "clean_up.py did not exit cleanly"
    assert "All modules imported successfully" in result.stdout, "Expected success message not found"