"""
Integration test for T030: Final Report Generation with Sensitivity Summary.

This test verifies that the final report generation script correctly:
1. Loads existing statistical, sensitivity, and robustness reports.
2. Calculates stability metrics.
3. Generates a summary.
4. Produces a valid JSON file at the expected path.
"""
import os
import json
import tempfile
import shutil
import pytest
from pathlib import Path

# We will mock the file paths by temporarily setting environment variables or 
# by creating a temporary directory structure that mimics the project layout.
# However, since the code uses hardcoded relative paths (data/results/...),
# we need to ensure those files exist in the test environment or mock the IO.
# For a true integration test, we will create temporary mock files.

@pytest.fixture
def mock_results_dir():
    """Create a temporary directory structure with mock result files."""
    temp_dir = tempfile.mkdtemp()
    results_dir = os.path.join(temp_dir, "data", "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Mock statistical report
    stat_report = {
        "p_value": 0.032,
        "is_significant": True,
        "cohens_d": 0.45,
        "t_statistic": 2.15,
        "df": 198
    }
    with open(os.path.join(results_dir, "statistical_report.json"), 'w') as f:
        json.dump(stat_report, f)
    
    # Mock sensitivity report
    sens_report = {
        "thresholds": [
            {"threshold": 0.01, "p_value": 0.032, "is_significant": False},
            {"threshold": 0.05, "p_value": 0.032, "is_significant": True},
            {"threshold": 0.10, "p_value": 0.032, "is_significant": True}
        ],
        "is_sensitive_to_threshold": False
    }
    with open(os.path.join(results_dir, "sensitivity_report.json"), 'w') as f:
        json.dump(sens_report, f)
    
    # Mock robustness report
    robust_report = {
        "summary": "Robustness check passed. Results hold after MMSE filtering.",
        "filtered_count": 15,
        "original_count": 200
    }
    with open(os.path.join(results_dir, "robustness_report.json"), 'w') as f:
        json.dump(robust_report, f)
    
    return temp_dir

def test_t030_generates_report(mock_results_dir):
    """Test that T030 script generates the final report correctly."""
    # Change to the mock directory to simulate project root
    original_cwd = os.getcwd()
    os.chdir(mock_results_dir)
    
    try:
        # Import the module under test (need to adjust path if necessary)
        # Assuming the test is run from the project root or the path is set up
        # We will execute the logic directly by importing the functions
        import sys
        sys.path.insert(0, os.path.join(original_cwd, "code"))
        
        from task_t030_final_report import compile_final_report, save_report, FINAL_REPORT_PATH
        
        # Run the compilation
        report = compile_final_report()
        
        # Assertions
        assert report is not None
        assert "metadata" in report
        assert "sensitivity_analysis" in report
        assert "statistical_results" in report
        assert "robustness_check" in report
        assert "overall_conclusion" in report
        
        # Check stability metrics
        stability = report["sensitivity_analysis"]["stability_metrics"]
        assert stability["stability_score"] == 2/3  # 2 out of 3 thresholds significant
        assert stability["stability_rating"] == "Medium" # 66% is >= 50% but < 80%
        
        # Check summary content
        summary = report["sensitivity_analysis"]["summary"]
        assert "significant" in summary.lower()
        
        # Save and verify file exists
        save_report(report, FINAL_REPORT_PATH)
        assert os.path.exists(FINAL_REPORT_PATH)
        
        # Verify JSON validity
        with open(FINAL_REPORT_PATH, 'r') as f:
            loaded = json.load(f)
        assert loaded == report

    finally:
        os.chdir(original_cwd)
        shutil.rmtree(mock_results_dir)

def test_t030_handles_missing_files():
    """Test that the script handles missing input files gracefully."""
    temp_dir = tempfile.mkdtemp()
    results_dir = os.path.join(temp_dir, "data", "results")
    os.makedirs(results_dir, exist_ok=True)
    
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        import sys
        sys.path.insert(0, os.path.join(original_cwd, "code"))
        
        # Reload to pick up new paths if cached, but since we use relative paths in code,
        # we rely on the current working directory.
        # We need to force re-import if the module was already imported with different paths
        # But for this simple logic, we can just call the function.
        
        from task_t030_final_report import compile_final_report
        
        report = compile_final_report()
        
        # Should not crash, but report should indicate missing data
        assert report["sensitivity_analysis"]["stability_metrics"]["reason"] is not None
        assert report["statistical_results"]["raw_data"] is None
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)