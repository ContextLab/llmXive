"""
Basic sanity test for the sensitivity analysis script.

The test checks that the script runs without raising an exception and that
it produces a JSON file containing entries for each threshold defined in
``RANSAC_THRESHOLDS``.
"""

import json
from pathlib import Path

import pytest

from eval.sensitivity import (
    RANSAC_THRESHOLDS,
    SENSITIVITY_OUTPUT_PATH,
    main,
)
from config import get_results_dir, ensure_directories

@pytest.fixture(scope="module", autouse=True)
def prepare_output_dir(tmp_path_factory):
    """
    Ensure the results directory exists and is writable for the test run.
    """
    results_dir = get_results_dir()
    ensure_directories(results_dir)
    # Clean any previous output.
    if SENSITIVITY_OUTPUT_PATH.is_file():
        SENSITIVITY_OUTPUT_PATH.unlink()
    yield
    # Cleanup after the test.
    if SENSITIVITY_OUTPUT_PATH.is_file():
        SENSITIVITY_OUTPUT_PATH.unlink()

def test_sensitivity_runs_and_creates_file(tmp_path):
    # Run the script – it should write the JSON file.
    main()

    # Verify the file exists.
    assert SENSITIVITY_OUTPUT_PATH.is_file(), "Output JSON was not created"

    # Load and validate its contents.
    with open(SENSITIVITY_OUTPUT_PATH, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    # The keys should correspond exactly to the thresholds (as strings).
    expected_keys = {str(t) for t in RANSAC_THRESHOLDS}
    assert set(data.keys()) == expected_keys, "Missing or extra thresholds in output"

    # Each entry must contain the two required metric fields.
    for entry in data.values():
        assert "world_score" in entry, "world_score missing in entry"
        assert "sparse_consistency_score" in entry, "sparse_consistency_score missing in entry"
        # Values should be numeric.
        assert isinstance(entry["world_score"], (int, float))
        assert isinstance(entry["sparse_consistency_score"], (int, float))