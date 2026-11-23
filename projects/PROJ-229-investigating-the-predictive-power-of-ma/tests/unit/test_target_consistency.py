"""
Unit test for the target consistency check (T005c).

The test simply runs the ``main`` function and asserts that the two
expected JSON artefacts are created and contain the required keys.
"""

import json
from pathlib import Path

import pytest

# Import the script entry point
from code.data.target_consistency_check import main as run_target_check

@pytest.fixture(scope="module")
def results_dir():
    """Ensure the results directory exists before the test runs."""
    path = Path("data/results")
    path.mkdir(parents=True, exist_ok=True)
    yield path
    # Cleanup after test – not strictly required but keeps the repo tidy
    for file in path.iterdir():
        if file.is_file():
            file.unlink()

def test_target_consistency_check_creates_outputs(results_dir):
    # Run the target consistency check
    run_target_check()

    target_path = results_dir / "target_decision.json"
    impute_path = results_dir / "imputation_rate_report.json"

    # Both files must exist
    assert target_path.is_file(), "target_decision.json was not created"
    assert impute_path.is_file(), "imputation_rate_report.json was not created"

    # Validate minimal schema
    with target_path.open() as fh:
        target_json = json.load(fh)
    with impute_path.open() as fh:
        impute_json = json.load(fh)

    # Required keys
    for key in ("target_name", "fallback_flag", "generated_at"):
        assert key in target_json, f"Missing key {key} in target_decision.json"

    for key in ("imputation_rate", "proxy_correlation", "fallback_flag", "generated_at"):
        assert key in impute_json, f"Missing key {key} in imputation_rate_report.json"

    # Types
    assert isinstance(target_json["target_name"], str)
    assert isinstance(target_json["fallback_flag"], bool)

    assert isinstance(impute_json["imputation_rate"], float)
    # proxy_correlation may be None if correlation could not be computed
    assert impute_json["proxy_correlation"] is None or isinstance(
        impute_json["proxy_correlation"], float
    )
    assert isinstance(impute_json["fallback_flag"], bool)