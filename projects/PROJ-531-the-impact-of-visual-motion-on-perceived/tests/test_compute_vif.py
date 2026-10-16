"""
Unit test for T015 – compute_vif.py

The test executes the script's ``main`` function and checks that:
  * ``data/processed/vif_report.json`` is created,
  * the JSON contains a ``vif_per_feature`` dictionary with numeric values,
  * the top‑level ``vif_pass`` flag is a boolean.
"""

import json
from pathlib import Path

import pytest

# Import the script as a module
from code.compute_vif import main as compute_vif_main, OUTPUT_JSON

@pytest.fixture(scope="session")
def ensure_input():
    """
    Ensure that the required input file exists for the test run.
    The repository already ships ``data/processed/analysis_ready.csv``.
    If it is missing, the test will fail loudly – this is intentional
    because the pipeline must provide the file before VIF can be computed.
    """
    input_path = Path("data/processed/analysis_ready.csv")
    assert input_path.exists(), "analysis_ready.csv missing; cannot run VIF test."
    return input_path

def test_compute_vif_creates_report(ensure_input):
    # Remove any existing report to guarantee a clean run
    if OUTPUT_JSON.exists():
        OUTPUT_JSON.unlink()

    # Run the VIF computation
    exit_code = compute_vif_main()
    assert exit_code == 0, "compute_vif script exited with non‑zero status"

    # Verify the output file exists
    assert OUTPUT_JSON.is_file(), "VIF report JSON was not created"

    # Load and validate the JSON structure
    with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
        report = json.load(f)

    # Expected top‑level keys
    assert "vif_per_feature" in report, "Missing 'vif_per_feature' in report"
    assert "vif_pass" in report, "Missing 'vif_pass' flag in report"

    # VIF values must be numeric
    for feat, val in report["vif_per_feature"].items():
        assert isinstance(val, (int, float)), f"VIF for {feat} is not numeric"

    # ``vif_pass`` must be a boolean
    assert isinstance(report["vif_pass"], bool), "'vif_pass' is not a boolean"

    # Optional sanity check: with only two predictors (latency & smoothness)
    # VIF values should be ≤ 5 in the synthetic dataset
    if report["vif_pass"]:
        # All VIFs below threshold
        for val in report["vif_per_feature"].values():
            assert val < 5.0, "Unexpected high VIF in synthetic data"