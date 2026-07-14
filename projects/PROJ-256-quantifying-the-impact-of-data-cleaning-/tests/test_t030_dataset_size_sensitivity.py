"""
Simple integration test for T030 – verifies that the script runs without
raising exceptions and produces the expected JSON output file.
"""

import json
from pathlib import Path

import pytest

from t030_dataset_size_sensitivity import main, OUTPUT_PATH

@pytest.mark.integration
def test_t030_runs_and_creates_output(tmp_path, monkeypatch):
    """
    The test redirects the output location to a temporary directory to avoid
    polluting the repository state.
    """
    # Redirect the global OUTPUT_PATH to a temp location.
    temp_output = tmp_path / "size_sensitivity.json"
    monkeypatch.setattr("t030_dataset_size_sensitivity.OUTPUT_PATH", temp_output)

    # Ensure any pre‑existing file is removed.
    if temp_output.exists():
        temp_output.unlink()

    # Run the script – it should complete without error.
    main()

    # Verify the file was created and contains valid JSON.
    assert temp_output.is_file(), "Output JSON file was not created."
    with temp_output.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic sanity checks on the JSON structure.
    assert isinstance(data, dict), "Output JSON should be a dict."
    for bin_name in ["small", "medium", "large"]:
        assert bin_name in data, f"Missing bin '{bin_name}' in output."
        assert "count" in data[bin_name], "Each bin must report a count."
