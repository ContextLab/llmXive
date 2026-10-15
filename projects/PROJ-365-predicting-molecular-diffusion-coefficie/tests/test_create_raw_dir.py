"""Test that ``code/create_raw_dir.py`` creates the ``data/raw`` directory."""

import subprocess
import sys
from pathlib import Path

def test_create_raw_dir():
    # Run the script
    result = subprocess.run(
        [sys.executable, "code/create_raw_dir.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script exited with {result.returncode}: {result.stderr}"

    raw_dir = Path("data/raw")
    assert raw_dir.is_dir(), "The directory data/raw was not created by the script"