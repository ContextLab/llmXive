"""
Unit tests for T015a: Success Rate Calculation.
Tests the logic of reading exclusion logs, manifest counts, and writing summary metrics.
"""
import os
import json
import csv
import tempfile
import shutil
import pytest

# Mock the paths module to use a temporary directory for testing
import code.data.paths as paths_module
from code.utils.success_rate import (
    calculate_success_rate,
    load_manifest,
    load_exclusion_log,
    write_summary_to_log,
    write_summary_to_json,
    run_success_rate_pipeline
)

@pytest.fixture
def temp_dir():
    """Creates a temporary directory for test artifacts."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)

@pytest.fixture
def setup_test_files(temp_dir):
    """Sets up mock manifest and exclusion log files."""
    # Create subdirectories
    processed_dir = os.path.join(temp_dir, "processed")
    raw_dir = os.path.join(temp_dir, "raw")
    results_dir = os.path.join(temp_dir, "results")
    os.makedirs(processed_dir)
    os.makedirs(raw_dir)
    os.makedirs(results_dir)

    # Mock Manifest
    manifest_data = {
        "subjects": [
            {"id": f"sub_{i:04d}", "status": "available"} for i in range(1, 101)
        ]
    }
    manifest_path = os.path.join(raw_dir, "hcp_manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f)

    # Mock Exclusion Log (T015/T017 output)
    exclusion_path = os.path.join(processed_dir, "exclusion_log.csv")
    with open(exclusion_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Subject_ID', 'Exclusion_Reason', 'Mean_FD'])
        writer.writeheader()
        # 10 subjects excluded
        for i in range(1, 11):
            writer.writerow({
                'Subject_ID': f"sub_{i:04d}",
                'Exclusion_Reason': 'Motion',
                'Mean_FD': '0.25'
            })

    # Patch the paths module functions to use temp_dir
    original_get_processed = paths_module.get_processed_path
    original_get_raw = paths_module.get_raw_path
    original_get_results = paths_module.get_results_path

    def mock_get_processed():
        return processed_dir
    def mock_get_raw():
        return raw_dir
    def mock_get_results():
        return results_dir

    paths_module.get_processed_path = mock_get_processed
    paths_module.get_raw_path = mock_get_raw
    paths_module.get_results_path = mock_get_results

    yield {
        "processed_dir": processed_dir,
        "raw_dir": raw_dir,
        "results_dir": results_dir,
        "exclusion_path": exclusion_path,
        "manifest_path": manifest_path
    }

    # Restore
    paths_module.get_processed_path = original_get_processed
    paths_module.get_raw_path = original_get_raw
    paths_module.get_results_path = original_get_results

def test_calculate_success_rate():
    assert calculate_success_rate(100, 10) == 0.9
    assert calculate_success_rate(100, 0) == 1.0
    assert calculate_success_rate(100, 100) == 0.0
    assert calculate_success_rate(0, 0) == 0.0

def test_load_exclusion_log(setup_test_files):
    rows = load_exclusion_log(setup_test_files["exclusion_path"])
    assert len(rows) == 10
    assert rows[0]['Subject_ID'] == 'sub_0001'
    assert rows[0]['Exclusion_Reason'] == 'Motion'

def test_write_summary_to_log(setup_test_files):
    exclusion_path = setup_test_files["exclusion_path"]
    summary_data = {"Pro_Processed": 0.9}
    
    write_summary_to_log(exclusion_path, summary_data)
    
    with open(exclusion_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Should have original 10 + 1 summary
    assert len(rows) == 11
    summary_row = rows[-1]
    assert summary_row['Subject_ID'] == 'SUMMARY'
    assert summary_row['Exclusion_Reason'] == 'Success_Rate'
    assert float(summary_row['Mean_FD']) == 0.9

def test_write_summary_to_json(setup_test_files):
    json_path = os.path.join(setup_test_files["results_dir"], "regression_summary.json")
    summary_data = {"Pro_Processed": 0.9, "Total_Subjects": 100}
    
    write_summary_to_json(json_path, summary_data)
    
    assert os.path.exists(json_path)
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    assert data['Pro_Processed'] == 0.9
    assert data['Total_Subjects'] == 100

def test_run_success_rate_pipeline(setup_test_files):
    """
    End-to-end test for the pipeline.
    Verifies that the summary is written to both CSV and JSON.
    """
    # Run the pipeline
    run_success_rate_pipeline()
    
    # Check CSV
    exclusion_path = setup_test_files["exclusion_path"]
    with open(exclusion_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 11
    assert rows[-1]['Subject_ID'] == 'SUMMARY'
    assert float(rows[-1]['Mean_FD']) == 0.9

    # Check JSON
    json_path = os.path.join(setup_test_files["results_dir"], "regression_summary.json")
    assert os.path.exists(json_path)
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    assert abs(data['Pro_Processed'] - 0.9) < 0.0001
    assert data['Total_Subjects'] == 100
    assert data['Excluded_Subjects'] == 10