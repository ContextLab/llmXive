"""
Contract test for the ``validate_regime_map.py`` script.

The test invokes the script on the generated PNG and asserts that it
exits with status 0.  If the PNG is missing, oversized, or lacks the
required labels, the script should exit with a non‑zero code, causing
the test to fail.
"""

import subprocess
import sys
from pathlib import Path

import pytest

@pytest.fixture(scope="module")
def png_path():
    # The PNG is produced by the analysis step; use the canonical location.
    return Path(__file__).resolve().parents[3] / "results" / "regime_map.png"

def test_validate_regime_map_success(png_path):
    """Run the validator; expect a zero exit code."""
    # Ensure the file exists before invoking the script.
    assert png_path.is_file(), f"Expected PNG at {png_path}"
    # Execute the script as a module.
    result = subprocess.run(
        [sys.executable, "code/validate_regime_map.py", str(png_path)],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Validator failed (code {result.returncode}). "
        f"Stdout: {result.stdout}\\nStderr: {result.stderr}"
    )