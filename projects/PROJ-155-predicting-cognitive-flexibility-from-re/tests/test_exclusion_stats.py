"""
Tests for T015a: Exclusion Statistics and Success Rate Calculation.
"""
import os
import json
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from code.utils.exclusion_stats import (
    calculate_success_rate,
    update_exclusion_log,
    update_regression_summary,
    get_total_subjects_from_manifest,
    run_success_rate_pipeline
)
from code.data.paths import get_processed_path, get_raw_path, get_results_path

@pytest.fixture
def mock_manifest(tmp_path):
    """Create a temporary manifest file."""
    manifest_data = {
        "subjects": [
            f"1001", f"1002", f"1003", f"1004", f"1005"
        ]
    }
    manifest_path = os.path.join(tmp_path, "manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f)
    return manifest_path

@pytest.fixture
def mock_exclusion_log(tmp_path):
    """Create a temporary exclusion log with some exclusions."""
    log_path = os.path.join(tmp_path, "exclusion_log.csv")
    data = {
        "Subject_ID": ["1002", "1004"],
        "Exclusion_Reason": ["Motion", "Missing_Behavioral_Score"],
        "Mean_FD": [0.25, 0.0]
    }
    df = pd.DataFrame(data)
    df.to_csv(log_path, index=False)
    return log_path

def test_get_total_subjects_from_manifest(mock_manifest):
    with patch('code.utils.exclusion_stats.get_raw_path', return_value=os.path.dirname(mock_manifest)):
        count = get_total_subjects_from_manifest()
        assert count == 5

def test_calculate_success_rate(mock_manifest, mock_exclusion_log):
    raw_dir = os.path.dirname(mock_manifest)
    proc_dir = os.path.dirname(mock_exclusion_log)
    
    with patch('code.utils.exclusion_stats.get_raw_path', return_value=raw_dir):
        with patch('code.utils.exclusion_stats.get_processed_path', return_value=proc_dir):
            metrics = calculate_success_rate()
            
            assert metrics["Total_Subjects"] == 5
            assert metrics["Excluded_Count"] == 2
            assert metrics["Processed_Count"] == 3
            assert abs(metrics["Pro_Processed"] - 0.6) < 1e-6

def test_update_exclusion_log(mock_exclusion_log):
    # Read original
    original_df = pd.read_csv(mock_exclusion_log)
    original_len = len(original_df)
    
    metrics = {"Pro_Processed": 0.6, "Total_Subjects": 5, "Excluded_Count": 2, "Processed_Count": 3}
    
    update_exclusion_log(metrics)
    
    # Read updated
    updated_df = pd.read_csv(mock_exclusion_log)
    assert len(updated_df) == original_len + 1
    assert updated_df.iloc[-1]["Subject_ID"] == "SUMMARY"
    assert updated_df.iloc[-1]["Exclusion_Reason"] == "Success_Rate_Calc"
    assert abs(updated_df.iloc[-1]["Mean_FD"] - 0.6) < 1e-6

def test_update_regression_summary(tmp_path):
    results_dir = str(tmp_path)
    summary_file = os.path.join(results_dir, "regression_summary.json")
    
    # Create initial empty file
    with open(summary_file, 'w') as f:
        json.dump({}, f)
    
    metrics = {"Pro_Processed": 0.6, "Total_Subjects": 5, "Excluded_Count": 2, "Processed_Count": 3}
    
    with patch('code.utils.exclusion_stats.get_results_path', return_value=results_dir):
        update_regression_summary(metrics)
    
    with open(summary_file, 'r') as f:
        data = json.load(f)
    
    assert data["SC_001_Success_Rate"] == 0.6
    assert data["Total_Subjects"] == 5

def test_run_success_rate_pipeline(mock_manifest, mock_exclusion_log):
    raw_dir = os.path.dirname(mock_manifest)
    proc_dir = os.path.dirname(mock_exclusion_log)
    results_dir = os.path.join(proc_dir, "..", "results")
    os.makedirs(results_dir, exist_ok=True)
    
    with patch('code.utils.exclusion_stats.get_raw_path', return_value=raw_dir):
        with patch('code.utils.exclusion_stats.get_processed_path', return_value=proc_dir):
            with patch('code.utils.exclusion_stats.get_results_path', return_value=results_dir):
                metrics = run_success_rate_pipeline()
                
                assert metrics["Pro_Processed"] == 0.6
                
                # Verify files were updated
                exclusion_log_path = os.path.join(proc_dir, "exclusion_log.csv")
                df = pd.read_csv(exclusion_log_path)
                assert df.iloc[-1]["Subject_ID"] == "SUMMARY"
                
                summary_file = os.path.join(results_dir, "regression_summary.json")
                with open(summary_file, 'r') as f:
                    reg_data = json.load(f)
                assert "SC_001_Success_Rate" in reg_data