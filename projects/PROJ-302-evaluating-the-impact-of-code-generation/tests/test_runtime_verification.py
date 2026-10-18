"""
Unit test for the runtime verification script.

The test imports ``code.verification.main`` and checks that after
execution the expected ``runtime_report.json`` file exists, contains
the correct keys and that every pipeline stage has an entry.
"""

import json
from pathlib import Path

import pytest

from code import verification
from llmxive_toolkit import paths

@pytest.fixture
def clean_report(tmp_path):
    """Ensure a clean environment – remove any pre‑existing report."""
    report_path = paths.data("processed", "runtime_report.json")
    if report_path.is_file():
        report_path.unlink()
    yield report_path
    # Cleanup after test
    if report_path.is_file():
        report_path.unlink()

def test_runtime_report_generated(clean_report: Path):
    """Run the verification script and validate the output JSON."""
    exit_code = verification.main()
    assert exit_code == 0, "Verification script should exit with status 0"

    # The script should have created the report at the canonical location.
    assert clean_report.is_file(), "runtime_report.json was not created"

    with clean_report.open("r", encoding="utf-8") as fp:
        data = json.load(fp)

    # Required top‑level keys.
    assert "stage_times" in data
    assert "total_seconds" in data

    # All expected stages must be present.
    expected_stages = [
        "data_acquisition",
        "prompt_engineering",
        "synthetic_generation",
        "feature_extraction",
        "timestamp_simulation",
        "matching",
        "analysis",
        "sensitivity",
        "visualization",
        "report_generation",
    ]
    missing = [s for s in expected_stages if s not in data["stage_times"]]
    assert not missing, f"Missing timing entries for stages: {missing}"

    # The total runtime must be a non‑negative number and respect the ceiling.
    assert isinstance(data["total_seconds"], (int, float))
    assert data["total_seconds"] >= 0
    assert data["total_seconds"] <= 21600, "Total runtime exceeds 6‑hour limit"