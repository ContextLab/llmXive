"""
Unit test for the pre‑study power analysis script.

This test ensures that:
1. The script executes without error.
2. The JSON report is created at the expected location.
3. The reported power meets the project requirement (≥ 0.8).
"""

import json
from pathlib import Path

from analysis.statistical_test import run_power_analysis

def test_run_power_analysis_creates_report(tmp_path: Path, monkeypatch):
    """
    Execute the power analysis and verify the output.
    """
    # Redirect the output path to a temporary directory to avoid polluting the repo.
    output_path = tmp_path / "pre_study_power.json"
    monkeypatch.setattr(
        "analysis.statistical_test.OUTPUT_PATH",
        output_path,
    )

    # Run the analysis.
    report = run_power_analysis()

    # The function should return the same dictionary that is written to disk.
    assert isinstance(report, dict), "Report should be a dict"

    # Verify the file exists.
    assert output_path.is_file(), f"Report file not found at {output_path}"

    # Load the JSON file and compare with the returned dict.
    with open(output_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    assert json_data == report, "JSON file content differs from returned report"

    # Check that the achieved power meets the required threshold.
    power = json_data["results"]["power_achieved_at_final_n"]
    assert power >= 0.8, f"Achieved power {power:.4f} is below the required 0.8"

    # Also ensure the constraint N >= 30 is satisfied.
    assert json_data["validation"]["constraint_N_ge_30"], "N constraint not satisfied"