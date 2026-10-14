"""
Minimal test for ``code/download_data.py``.

The test verifies that the script aborts with a clear error when the
availability report does not list any datasets. This behaviour is required
because the pipeline cannot continue without a real data source.
"""

import sys
import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# Import the module under test.
from code.download_data import main as download_main

@pytest.fixture
def empty_report(tmp_path, monkeypatch):
    """Create an empty availability_report.json in a temporary data directory."""
    # Redirect the llmxive_toolkit paths to the temporary location.
    # ``paths.data`` creates folders under the project root; we monkeypatch its
    # ``root`` attribute so that all data paths resolve inside ``tmp_path``.
    original_root = paths.root
    monkeypatch.setattr(paths, "root", tmp_path, raising=False)

    report_path = paths.data("source", "availability_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({"datasets": []}), encoding="utf-8")
    yield report_path
    # Restore original root after the test.
    monkeypatch.setattr(paths, "root", original_root, raising=False)

def test_download_exits_when_no_datasets(empty_report, capsys):
    """
    Ensure the script exits with a non‑zero status and logs an appropriate
    error message when the availability report contains no datasets.
    """
    with pytest.raises(SystemExit) as excinfo:
        download_main()
    # The script should exit with code 1.
    assert excinfo.value.code == 1

    captured = capsys.readouterr()
    assert "No datasets with the required variables were found" in captured.err