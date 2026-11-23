"""
Integration test for T048: Final Statistical Report Generation.
Verifies that the report generator runs successfully on real data and produces valid output.
"""

import os
import json
import tempfile
import shutil
import pytest
import csv
from pathlib import Path

# Import the module under test
from stats.report_generator import (
    load_paired_dataset, 
    run_statistical_tests, 
    generate_report_markdown, 
    main
)

@pytest.fixture
def sample_paired_dataset(tmp_path):
    """Create a temporary sample paired dataset."""
    data_path = tmp_path / "final_paired_dataset.csv"
    rows = [
        {"task_id": "1", "task_type": "occlusion", "2d_success_rate": "0.8", "2d_mean_latency": "100.0", "3d_success": "1.0", "3d_latency": "80.0", "success_diff": "-0.2", "latency_diff": "20.0"},
        {"task_id": "2", "task_type": "occlusion", "2d_success_rate": "0.9", "2d_mean_latency": "110.0", "3d_success": "1.0", "3d_latency": "90.0", "success_diff": "-0.1", "latency_diff": "20.0"},
        {"task_id": "3", "task_type": "depth", "2d_success_rate": "0.5", "2d_mean_latency": "120.0", "3d_success": "1.0", "3d_latency": "70.0", "success_diff": "-0.5", "latency_diff": "50.0"},
        {"task_id": "4", "task_type": "depth", "2d_success_rate": "0.4", "2d_mean_latency": "130.0", "3d_success": "1.0", "3d_latency": "75.0", "success_diff": "-0.6", "latency_diff": "55.0"},
        {"task_id": "5", "task_type": "relative", "2d_success_rate": "0.7", "2d_mean_latency": "105.0", "3d_success": "0.8", "3d_latency": "85.0", "success_diff": "-0.1", "latency_diff": "20.0"},
    ]
    
    with open(data_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    
    return data_path

@pytest.fixture
def sample_sensitivity_data(tmp_path):
    """Create a temporary sample sensitivity data file."""
    data_path = tmp_path / "depth_threshold_sweep.csv"
    rows = [
        {"threshold_value": "0.1", "false_positive_rate": "0.05", "false_negative_rate": "0.10"},
        {"threshold_value": "0.5", "false_positive_rate": "0.10", "false_negative_rate": "0.05"},
        {"threshold_value": "1.0", "false_positive_rate": "0.15", "false_negative_rate": "0.02"},
    ]
    
    with open(data_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    
    return data_path

def test_load_paired_dataset(sample_paired_dataset):
    """Test loading the paired dataset."""
    data = load_paired_dataset(str(sample_paired_dataset))
    assert len(data) == 5
    assert data[0]['task_type'] == 'occlusion'
    assert data[0]['2d_success_rate'] == 0.8

def test_run_statistical_tests(sample_paired_dataset):
    """Test running statistical tests on the dataset."""
    data = load_paired_dataset(str(sample_paired_dataset))
    results = run_statistical_tests(data)
    
    assert 'task_types' in results
    assert 'occlusion' in results['task_types']
    assert 'depth' in results['task_types']
    assert 'relative' in results['task_types']
    
    # Check that tests were attempted
    occlusion_res = results['task_types']['occlusion']
    assert 'mcnemar' in occlusion_res
    assert 'wilcoxon' in occlusion_res

def test_generate_report_markdown(sample_paired_dataset, sample_sensitivity_data, tmp_path):
    """Test report generation."""
    # Temporarily override paths for the test
    import stats.report_generator as rg
    original_input = rg.INPUT_DATASET_PATH
    original_sens = rg.SENSITIVITY_INPUT_PATH
    original_output = rg.OUTPUT_REPORT_PATH
    
    rg.INPUT_DATASET_PATH = str(sample_paired_dataset)
    rg.SENSITIVITY_INPUT_PATH = str(sample_sensitivity_data)
    report_path = str(tmp_path / "test_report.md")
    rg.OUTPUT_REPORT_PATH = report_path
    
    try:
        data = load_paired_dataset(str(sample_paired_dataset))
        sens_data = rg.load_sensitivity_data() # Load from temp path
        stats_res = run_statistical_tests(data)
        
        report = generate_report_markdown(stats_res, sens_data)
        
        assert "# Final Statistical Report" in report
        assert "## Executive Summary" in report
        assert "## Statistical Test Results" in report
        assert "## Sensitivity Analysis" in report
        assert "Bonferroni" in report
        
        # Write to file to ensure it's valid markdown
        with open(report_path, 'w') as f:
            f.write(report)
        
        assert os.path.exists(report_path)
    finally:
        # Restore original paths
        rg.INPUT_DATASET_PATH = original_input
        rg.SENSITIVITY_INPUT_PATH = original_sens
        rg.OUTPUT_REPORT_PATH = original_output

def test_main_execution(sample_paired_dataset, sample_sensitivity_data, tmp_path, monkeypatch):
    """Test the main entry point."""
    import stats.report_generator as rg
    
    # Setup temp paths
    rg.INPUT_DATASET_PATH = str(sample_paired_dataset)
    rg.SENSITIVITY_INPUT_PATH = str(sample_sensitivity_data)
    report_path = str(tmp_path / "final_report.md")
    json_path = str(tmp_path / "stats.json")
    rg.OUTPUT_REPORT_PATH = report_path
    rg.OUTPUT_STATS_JSON_PATH = json_path
    
    # Mock os.makedirs to work in temp dir
    original_makedirs = os.makedirs
    def mock_makedirs(path, *args, **kwargs):
        # Ensure we are writing to tmp_path
        if path.startswith("results"):
            path = str(tmp_path / path.replace("results", ""))
        return original_makedirs(path, *args, **kwargs)
    
    monkeypatch.setattr(os, 'makedirs', mock_makedirs)
    
    exit_code = main()
    
    assert exit_code == 0
    assert os.path.exists(report_path)
    assert os.path.exists(json_path)
    
    # Verify content
    with open(report_path, 'r') as f:
        content = f.read()
    assert "Conclusion" in content
    assert "Task Type" in content
