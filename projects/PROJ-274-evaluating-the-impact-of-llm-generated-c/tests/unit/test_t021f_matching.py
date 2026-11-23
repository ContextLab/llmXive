import json
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from run_matching_report import (
    calculate_baseline_stats,
    filter_by_thresholds,
    DATA_RAW_DIR,
    LOC_FILE,
    CC_FILE,
    RUBRIC_INTERMEDIATE_FILE,
    OUTPUT_SELECTION_FILE,
    OUTPUT_REPORT_FILE
)
from validation import save_json_file

@pytest.fixture
def temp_data_dir():
    """Creates a temporary directory structure for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Override globals for this test context
        global DATA_RAW_DIR, LOC_FILE, CC_FILE, RUBRIC_INTERMEDIATE_FILE
        global OUTPUT_SELECTION_FILE, OUTPUT_REPORT_FILE

        original_dir = DATA_RAW_DIR
        original_loc = LOC_FILE
        original_cc = CC_FILE
        original_rubric = RUBRIC_INTERMEDIATE_FILE
        original_sel = OUTPUT_SELECTION_FILE
        original_rep = OUTPUT_REPORT_FILE

        DATA_RAW_DIR = tmp_path
        LOC_FILE = tmp_path / "repo_loc_raw.json"
        CC_FILE = tmp_path / "repo_cc_raw.json"
        RUBRIC_INTERMEDIATE_FILE = tmp_path / "repo_selection_rubric_intermediate.json"
        OUTPUT_SELECTION_FILE = tmp_path / "repo_selection_rubric.json"
        OUTPUT_REPORT_FILE = tmp_path / "repo_matching_report.json"

        yield tmp_path

        # Restore
        DATA_RAW_DIR = original_dir
        LOC_FILE = original_loc
        CC_FILE = original_cc
        RUBRIC_INTERMEDIATE_FILE = original_rubric
        OUTPUT_SELECTION_FILE = original_sel
        OUTPUT_REPORT_FILE = original_rep

def test_calculate_baseline_stats():
    """Test median calculation logic."""
    metrics = {
        "repo_a": {"loc": 100, "cc": 10},
        "repo_b": {"loc": 200, "cc": 20},
        "repo_c": {"loc": 300, "cc": 30}
    }
    baseline = calculate_baseline_stats(metrics)
    assert baseline["median_loc"] == 200
    assert baseline["median_cc"] == 20

def test_filter_by_thresholds_accept():
    """Test that repos within 15% are accepted."""
    metrics = {
        "repo_a": {"loc": 200, "cc": 20} # Exactly median
    }
    baseline = {"median_loc": 200, "median_cc": 20}
    accepted, rejected, details = filter_by_thresholds(metrics, baseline)
    
    assert "repo_a" in accepted
    assert "repo_a" not in rejected
    assert details[0]["status"] == "accepted"

def test_filter_by_thresholds_reject_loc():
    """Test that repos outside 15% on LOC are rejected."""
    # Median 200. Range [170, 230].
    # 300 is outside.
    metrics = {
        "repo_b": {"loc": 300, "cc": 20}
    }
    baseline = {"median_loc": 200, "median_cc": 20}
    accepted, rejected, details = filter_by_thresholds(metrics, baseline)
    
    assert "repo_b" not in accepted
    assert "repo_b" in rejected
    assert details[0]["status"] == "rejected"
    assert "LOC" in details[0]["reason"]

def test_filter_by_thresholds_reject_cc():
    """Test that repos outside 15% on CC are rejected."""
    # Median 20. Range [17, 23].
    # 50 is outside.
    metrics = {
        "repo_c": {"loc": 200, "cc": 50}
    }
    baseline = {"median_loc": 200, "median_cc": 20}
    accepted, rejected, details = filter_by_thresholds(metrics, baseline)
    
    assert "repo_c" not in accepted
    assert "repo_c" in rejected
    assert details[0]["status"] == "rejected"
    assert "CC" in details[0]["reason"]

def test_full_integration(temp_data_dir):
    """
    End-to-end test: Create input files, run logic, verify output files exist.
    """
    # Prepare input data
    loc_data = {
        "repo_good": {"total": 200},
        "repo_bad_loc": {"total": 500},
        "repo_bad_cc": {"total": 200}
    }
    cc_data = {
        "repo_good": {"total": 20},
        "repo_bad_loc": {"total": 20},
        "repo_bad_cc": {"total": 100} # High CC
    }
    rubric_data = {
        "repo_good": 3,
        "repo_bad_loc": 3,
        "repo_bad_cc": 3
    }

    save_json_file(LOC_FILE, loc_data)
    save_json_file(CC_FILE, cc_data)
    save_json_file(RUBRIC_INTERMEDIATE_FILE, rubric_data)

    # Import the helper functions that rely on the global paths
    # We need to re-import or call the logic directly since globals changed
    from run_matching_report import load_metrics_data, calculate_baseline_stats, filter_by_thresholds

    metrics = load_metrics_data()
    assert "repo_good" in metrics
    assert "repo_bad_loc" in metrics
    assert "repo_bad_cc" in metrics

    baseline = calculate_baseline_stats(metrics)
    # Median LOC: [200, 200, 500] -> 200. Median CC: [20, 20, 100] -> 20.
    assert baseline["median_loc"] == 200
    assert baseline["median_cc"] == 20

    accepted, rejected, details = filter_by_thresholds(metrics, baseline)

    # repo_good (200, 20) -> Accept
    # repo_bad_loc (500, 20) -> Reject (LOC)
    # repo_bad_cc (200, 100) -> Reject (CC)
    assert "repo_good" in accepted
    assert "repo_bad_loc" in rejected
    assert "repo_bad_cc" in rejected

    # Verify file writing logic (simulating main() behavior)
    save_json_file(OUTPUT_SELECTION_FILE, accepted)
    
    report_payload = {
        "baseline_stats": baseline,
        "details": details
    }
    save_json_file(OUTPUT_REPORT_FILE, report_payload)

    # Assert files exist
    assert OUTPUT_SELECTION_FILE.exists()
    assert OUTPUT_REPORT_FILE.exists()

    # Verify content
    with open(OUTPUT_SELECTION_FILE) as f:
        saved_accepted = json.load(f)
    assert "repo_good" in saved_accepted
    assert len(saved_accepted) == 1

    with open(OUTPUT_REPORT_FILE) as f:
        saved_report = json.load(f)
    assert saved_report["details"][0]["status"] == "accepted"
    assert saved_report["details"][1]["status"] == "rejected"