"""
Contract test for the precision validation output.

The test verifies that the ``code.analysis.precision`` module can be executed
end‑to‑end and that it produces the expected artefacts:

* ``data/precision_report.json`` – a JSON report containing validation
  statistics.
* ``data/plots/crossing_vs_braid.png`` – a scatter plot of crossing number
  versus braid index stratified by alternating classification.

The test is deliberately lightweight: it only checks for the existence of
the files and that the JSON content contains the required top‑level keys.
"""

import json
from pathlib import Path

import pytest

# Import the module under test
from analysis.precision import main as precision_main

@pytest.fixture(scope="module")
def run_precision():
    """Execute the precision pipeline once for the whole test module."""
    # Ensure a clean environment – the pipeline itself creates missing data.
    precision_main()
    yield
    # No teardown required; artefacts are left for downstream inspection.

def test_precision_report_exists(run_precision):
    report_path = Path("data/precision_report.json")
    assert report_path.is_file(), f"Expected report at {report_path}"
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic contract: required keys must be present
    required_keys = {"total_records", "valid_crossing_number", "valid_braid_index", "issues", "generated_at"}
    missing = required_keys - data.keys()
    assert not missing, f"Missing keys in precision report: {missing}"

def test_crossing_vs_braid_plot_exists(run_precision):
    plot_path = Path("data/plots/crossing_vs_braid.png")
    assert plot_path.is_file(), f"Expected plot at {plot_path}"
    # Simple sanity check: file size should be > 0 bytes
    assert plot_path.stat().st_size > 0, "Plot file appears to be empty"