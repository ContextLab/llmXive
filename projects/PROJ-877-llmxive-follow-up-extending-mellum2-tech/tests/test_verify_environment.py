"""
Unit tests for the ``code.verify_environment`` script.

The tests ensure that the script runs without raising an exception
and that it writes the expected JSON report file.
"""

import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

@pytest.fixture
def report_path(tmp_path: Path) -> Path:
    # The script writes to the project's data/results directory.
    # Ensure the path exists and is writable.
    out = paths.data("results", "environment_check.json")
    # Remove any existing file to start fresh.
    if out.is_file():
        out.unlink()
    return out

def test_verify_environment_runs_successfully(report_path: Path):
    """
    Execute the script via its ``main`` function and verify:
    * Exit code is 0.
    * The JSON report file is created.
    * The ``config_import`` entry reports ``ok: True``.
    """
    from code.verify_environment import main

    exit_code = main()
    assert exit_code == 0, "Script should exit with status 0 when config is valid"

    # The report must exist and be valid JSON.
    assert report_path.is_file(), "Report file was not created"
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data.get("config_import", {}).get("ok") is True
    # The script should always include the pinned packages section.
    assert "pinned_packages" in data