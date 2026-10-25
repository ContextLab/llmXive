"""
Unit tests for ``code/fetch_cochrane_data.py``.
The tests verify that the script raises ``FileNotFoundError`` when
the URL cannot be reached and that it successfully writes a CSV file
when a reachable URL is supplied.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# Ensure the project root is on the import path.
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from fetch_cochrane_data import (
    load_jackson_2010_base_data,
    validate_data_structure,
    save_to_csv,
    main,
)

# A tiny CSV payload that satisfies the required schema.
_SAMPLE_CSV = """study_id,effect,se,n
s1,0.2,0.05,30
s2,-0.1,0.07,25
"""

def _mock_urlopen_success(*args, **kwargs):
    """Mimic ``urllib.request.urlopen`` returning a successful response."""
    mock_resp = mock.Mock()
    mock_resp.read.return_value = _SAMPLE_CSV.encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None
    return mock_resp

def _mock_urlopen_failure(*args, **kwargs):
    """Mimic ``urllib.request.urlopen`` raising a URLError."""
    raise urllib.error.URLError("mocked connection failure")

def test_load_success():
    with mock.patch("urllib.request.urlopen", side_effect=_mock_urlopen_success):
        data = load_jackson_2010_base_data("http://example.com/cochrane.csv")
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["study_id"] == "s1"

def test_load_failure_raises():
    with mock.patch("urllib.request.urlopen", side_effect=_mock_urlopen_failure):
        with pytest.raises(FileNotFoundError):
            load_jackson_2010_base_data("http://nonexistent.example.com/file.csv")

def test_validate_structure_ok():
    # Use the same sample data as ``load_jackson_2010_base_data`` would return.
    data = [
        {"study_id": "s1", "effect": "0.2", "se": "0.05", "n": "30"},
        {"study_id": "s2", "effect": "-0.1", "se": "0.07", "n": "25"},
    ]
    assert validate_data_structure(data) is True

def test_validate_structure_missing_column():
    data = [{"study_id": "s1", "effect": "0.2", "se": "0.05"}]  # missing ``n``
    assert validate_data_structure(data) is False

def test_save_to_csv_creates_file(tmp_path):
    out_file = tmp_path / "out.csv"
    data = [
        {"study_id": "s1", "effect": "0.2", "se": "0.05", "n": "30"},
        {"study_id": "s2", "effect": "-0.1", "se": "0.07", "n": "25"},
    ]
    save_to_csv(data, str(out_file))
    assert out_file.is_file()
    content = out_file.read_text(encoding="utf-8")
    assert "study_id,effect,se,n" in content

def test_main_successful_run(monkeypatch, tmp_path):
    # Patch ``urllib.request.urlopen`` to return a valid CSV.
    monkeypatch.setattr(
        "urllib.request.urlopen", _mock_urlopen_success
    )
    out_file = tmp_path / "downloaded.csv"
    test_args = ["fetch_cochrane_data.py", "--url", "http://example.com/file.csv", "--out", str(out_file)]
    monkeypatch.setattr(sys, "argv", test_args)
    exit_code = main()
    assert exit_code == 0
    assert out_file.is_file()
    assert out_file.read_text().strip().startswith("study_id,effect,se,n")

def test_main_failure_raises(monkeypatch, tmp_path):
    # Force a URL error.
    monkeypatch.setattr(
        "urllib.request.urlopen", _mock_urlopen_failure
    )
    out_file = tmp_path / "should_not_exist.csv"
    test_args = ["fetch_cochrane_data.py", "--url", "http://bad.url/file.csv", "--out", str(out_file)]
    monkeypatch.setattr(sys, "argv", test_args)
    exit_code = main()
    assert exit_code == 1
    assert not out_file.exists()