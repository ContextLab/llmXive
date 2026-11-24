"""
Unit test for the ``validate_cochrane_download.py`` script.

The test checks that the script exits with a non‑zero status code when the
URL is unreachable, satisfying the verification requirement for task
**T001a**.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.timeout(60)
def test_invalid_url(monkeypatch):
    """
    Run the validator against a deliberately invalid URL and assert that
    it fails with exit code 1 (FileNotFoundError path).
    """
    repo_root = Path(__file__).resolve().parents[2]
    # Use a URL that is guaranteed to fail (e.g., a non‑existent domain).
    invalid_url = "https://this-domain-does-not-exist-12345.org/missing.csv"

    result = subprocess.run(
        [sys.executable, "code/scripts/validate_cochrane_download.py",
         "--url", invalid_url],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # The script should exit with a non‑zero code and print an error.
    assert result.returncode != 0, "Script should have failed for an invalid URL"
    assert "ERROR" in result.stderr.upper()
