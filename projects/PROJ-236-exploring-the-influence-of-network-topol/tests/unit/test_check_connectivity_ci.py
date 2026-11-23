"""
Unit tests for the CI connectivity‑gate implementation (code/ci/check_connectivity.py).
The tests verify that the helper functions correctly interpret the various
JSON formats and that ``main`` exits with the appropriate status code.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

# Import the module under test
from ci.check_connectivity import load_metrics, get_success_rate, main, REQUIRED_SUCCESS_RATE


@pytest.fixture
def tmp_metrics_file(tmp_path: Path):
    """Utility fixture that writes a JSON file and returns its Path."""
    def _writer(content):
        p = tmp_path / "metrics.json"
        p.write_text(json.dumps(content), encoding="utf-8")
        return p
    return _writer


def test_load_metrics_explicit_counts(tmp_metrics_file):
    path = tmp_metrics_file({"total": 100, "successful": 96})
    metrics = load_metrics(path)
    assert metrics == {"total": 100, "successful": 96}


def test_load_metrics_boolean_list(tmp_metrics_file):
    path = tmp_metrics_file([True, False, True, True])
    metrics = load_metrics(path)
    assert metrics == {"total": 4, "successful": 3}


def test_load_metrics_dict_list(tmp_metrics_file):
    data = [
        {"realization_id": 1, "connected": True},
        {"realization_id": 2, "connected": False},
        {"realization_id": 3, "connected": True},
    ]
    path = tmp_metrics_file(data)
    metrics = load_metrics(path)
    assert metrics == {"total": 3, "successful": 2}


def test_get_success_rate():
    assert get_success_rate({"total": 20, "successful": 19}) == pytest.approx(0.95)
    assert get_success_rate({"total": 10, "successful": 10}) == 1.0


def test_main_success(monkeypatch, tmp_metrics_file, capsys):
    """When the success rate meets the threshold, ``main`` exits with code 0."""
    path = tmp_metrics_file({"total": 100, "successful": 96})
    # Monkey‑patch sys.argv for the script
    monkeypatch.setattr(sys, "argv", ["check_connectivity.py", str(path)])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "SUCCESS" in captured.out


def test_main_failure(monkeypatch, tmp_metrics_file, capsys):
    """When the success rate is below the threshold, ``main`` exits with code 1."""
    path = tmp_metrics_file({"total": 100, "successful": 90})
    monkeypatch.setattr(sys, "argv", ["check_connectivity.py", str(path)])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "FAILURE" in captured.err


def test_main_missing_file(monkeypatch, capsys):
    """A missing metrics file should cause a non‑zero exit."""
    monkeypatch.setattr(sys, "argv", ["check_connectivity.py", "nonexistent.json"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "ERROR" in captured.err