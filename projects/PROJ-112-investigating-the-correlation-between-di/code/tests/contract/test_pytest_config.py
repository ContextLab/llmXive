"""
Contract test to ensure pytest configuration is valid and discoverable.
"""
import pytest
import subprocess
import sys
from pathlib import Path

def test_pytest_discoverable():
    """Test that pytest can discover tests in the project."""
    # Run pytest with --collect-only to see if it finds tests without running them
    pytest_path = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(pytest_path), "--collect-only", "-q"],
        capture_output=True,
        text=True
    )
    # We expect at least some tests to be found (including this one)
    assert result.returncode == 0, f"Pytest collection failed: {result.stderr}"
    assert "collected" in result.stdout or result.returncode == 0