"""
Unit test for the ``validate_cochrane_csv.py`` script.

The test ensures that the script raises ``FileNotFoundError`` when the
supplied URL cannot be reached and exits cleanly when the URL is
reachable (using a mocked successful download).
"""

import sys
from pathlib import Path
from unittest import mock

import pytest

# Ensure project root is on import path.
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from code.scripts.validate_cochrane_csv import main

def _mock_success(*args, **kwargs):
    """Mock ``load_jackson_2010_base_data`` to return dummy data."""
    return [{"study_id": "s1", "effect": "0.1", "se": "0.02", "n": "30"}]

def _mock_failure(*args, **kwargs):
    """Mock ``load_jackson_2010_base_data`` to raise FileNotFoundError."""
    raise FileNotFoundError("mocked connection failure")

def test_validate_success(monkeypatch):
    """The script should exit with code 0 when the URL is reachable."""
    monkeypatch.setattr(
        "fetch_cochrane_data.load_jackson_2010_base_data", _mock_success
    )
    exit_code = main(["--url", "http://example.com/cochrane.csv"])
    assert exit_code == 0

def test_validate_failure(monkeypatch):
    """The script must raise FileNotFoundError when the URL is unreachable."""
    monkeypatch.setattr(
        "fetch_cochrane_data.load_jackson_2010_base_data", _mock_failure
    )
    with pytest.raises(FileNotFoundError):
        main(["--url", "http://nonexistent.example.com/file.csv"])