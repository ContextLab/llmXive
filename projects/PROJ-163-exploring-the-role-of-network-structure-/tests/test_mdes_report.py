"""
Simple test to ensure that the MDES computation creates the expected JSON report.
"""

import os
import json
import pytest

from code.stats_engine import compute_mdes

@pytest.fixture
def clean_report(tmp_path):
    # Ensure no leftover report exists
    report_path = tmp_path / "mdes_report.json"
    if report_path.exists():
        report_path.unlink()
    return str(report_path)

def test_compute_mdes_writes_report(clean_report):
    result = compute_mdes(n=30, power=0.8, alpha=0.05, output_path=clean_report)

    # Verify the function returns a dict with required keys
    assert isinstance(result, dict)
    for key in ["sample_size", "power", "alpha", "minimum_detectable_effect", "confidence_interval", "low_power_flag"]:
        assert key in result

    # Verify the JSON file was written and matches the returned dict
    assert os.path.exists(clean_report)
    with open(clean_report, "r") as f:
        data = json.load(f)
    assert data == result