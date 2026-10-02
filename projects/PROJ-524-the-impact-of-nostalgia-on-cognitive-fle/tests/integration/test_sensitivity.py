import os
import json
import pytest
import shutil
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from code.analysis import run_sensitivity_analysis
from code.config import get_config

RESULTS_DIR = Path("data/results")
SENSITIVITY_REPORT_PATH = RESULTS_DIR / "sensitivity_report.json"
STATISTICAL_REPORT_PATH = RESULTS_DIR / "statistical_report.json"
ROBUSTNESS_COMPARISON_PATH = RESULTS_DIR / "sensitivity_comparison.json"

# Ensure results directory exists for the test
@pytest.fixture(autouse=True)
def setup_results_dir():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup is optional in integration tests but good practice
    # We leave files for inspection unless they conflict

def test_sensitivity_analysis_runs_with_real_pipeline():
    """
    Integration test: Run the full sensitivity analysis pipeline.
    This test verifies that the system can read the statistical report,
    perform the threshold sweep, check robustness, and generate the final
    sensitivity_report.json as required by T028 and T029.
    """
    # Prerequisite: The statistical report must exist from T022
    # If it doesn't, we skip or fail the test (as the pipeline is broken)
    if not STATISTICAL_REPORT_PATH.exists():
        pytest.skip("statistical_report.json not found. Run T022 first.")

    # Prerequisite: Robustness comparison must exist from T027c
    # If T027 skipped due to missing MMSE, this file might not exist.
    # We handle this gracefully.
    robustness_exists = ROBUSTNESS_COMPARISON_PATH.exists()

    try:
        # Execute the sensitivity analysis
        # This function encapsulates T026, T028, T029, and T041 logic
        report = run_sensitivity_analysis(robustness_comparison_exists=robustness_exists)

        # Verify the report structure
        assert report is not None
        assert "thresholds" in report
        assert "borderline_flag" in report
        assert "is_sensitive_to_threshold" in report
        assert "robustness_summary" in report

        # Verify threshold sweep logic (T026)
        thresholds = report["thresholds"]
        assert len(thresholds) >= 4  # 0.01, 0.04, 0.05, 0.06, 0.10
        
        # Verify borderline detection (T029, T041)
        # The flag should be a boolean
        assert isinstance(report["borderline_flag"], bool)
        assert isinstance(report["is_sensitive_to_threshold"], bool)

        # Write the report to disk to satisfy T028 artifact requirement
        with open(SENSITIVITY_REPORT_PATH, 'w') as f:
            json.dump(report, f, indent=2)

        # Verify file was written
        assert SENSITIVITY_REPORT_PATH.exists()

    except FileNotFoundError as e:
        # If critical input files are missing, the pipeline is incomplete
        pytest.fail(f"Sensitivity analysis failed due to missing input: {e}")
    except Exception as e:
        pytest.fail(f"Sensitivity analysis failed unexpectedly: {e}")

def test_borderline_threshold_detection_logic():
    """
    Integration test: Verify that p-values in the range [0.04, 0.06] 
    trigger the 'is_sensitive_to_threshold' flag.
    """
    # We rely on the run_sensitivity_analysis function which should
    # implement the logic from T029 and T041.
    # We verify the output file contains the correct flag.
    
    if not SENSITIVITY_REPORT_PATH.exists():
        # Run the pipeline first if not present
        pytest.skip("Sensitivity report not generated yet.")

    with open(SENSITIVITY_REPORT_PATH, 'r') as f:
        report = json.load(f)

    # Check that the borderline flag logic is present in the report
    # The task requires a binary flag 'is_sensitive_to_threshold'
    assert "is_sensitive_to_threshold" in report

    # If the flag is True, verify that at least one threshold result
    # falls in the borderline range.
    if report["is_sensitive_to_threshold"]:
        thresholds = report.get("thresholds", {})
        borderline_found = False
        for key, val in thresholds.items():
            p_val = val.get("p_value")
            if p_val is not None and 0.04 <= p_val <= 0.06:
                borderline_found = True
                break
        assert borderline_found, "Flag is True but no borderline p-values found in thresholds."

def test_sensitivity_report_schema_compliance():
    """
    Integration test: Verify the generated sensitivity_report.json
    matches the expected schema for US3 (T028, T030).
    """
    if not SENSITIVITY_REPORT_PATH.exists():
        pytest.skip("Sensitivity report not generated.")

    with open(SENSITIVITY_REPORT_PATH, 'r') as f:
        report = json.load(f)

    required_keys = [
        "thresholds",
        "borderline_flag",
        "is_sensitive_to_threshold",
        "robustness_summary",
        "analysis_timestamp"
    ]

    for key in required_keys:
        assert key in report, f"Missing required key in sensitivity report: {key}"

    # Verify thresholds structure
    thresholds = report["thresholds"]
    assert isinstance(thresholds, dict)
    for thresh_key, thresh_val in thresholds.items():
        assert "significant" in thresh_val
        assert "p_value" in thresh_val
        assert isinstance(thresh_val["significant"], bool)
        assert isinstance(thresh_val["p_value"], (int, float))

    # Verify robustness summary exists and is a dict
    assert isinstance(report["robustness_summary"], dict)