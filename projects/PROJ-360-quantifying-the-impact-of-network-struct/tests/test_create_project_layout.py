"""
Test that the `create_project_layout.py` script creates the expected directories.
"""

import sys
import subprocess
from pathlib import Path

from llmxive_toolkit import paths

def test_create_project_layout():
    """Run the layout script and verify directories exist."""
    # Run the script
    result = subprocess.run(
        [sys.executable, "code/create_project_layout.py"],
        capture_output=True,
        text=True,
        cwd=Path.cwd()
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify each required directory exists
    assert paths.data("processed").exists(), "data/processed/ was not created"
    assert paths.models().exists(), "models/ was not created"
    assert paths.results().exists(), "results/ was not created"
    # `paths.code()` points to the existing `code/` directory where the script lives
    assert paths.code().exists(), "code/ was not created"