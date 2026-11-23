"""
Unit tests for the post-run parity verification module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

from src.analysis.parity_checker import (
    ParityVerificationError,
    RunParityRecord,
    ParityReport,
    load_single_run_metrics,
    extract_evaluation_count,
    extract_condition_from_path,
    collect_all_run_metrics,
    generate_parity_report,
    save_parity_report
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir) / "results"
        results_dir.mkdir()
        
        # Create mock run directories
        for cond in ['sequential', 'mixed', 'coevolving']:
            for i in range(3):
                run_dir = results_dir / f"run_{cond}_{i}"
                run_dir.mkdir()
                
                metrics = {
                    "total_rule_evaluations": 1000,
                    "accuracy": 0.95,
                    "condition": cond,
                    "seed": i
                }
                with open(run_dir / "final_metrics.json", 'w') as f:
                    json.dump(metrics, f)
        
        yield Path(tmpdir)

def test_load_single_run_metrics_success(temp_data_dir):
    """Test successful loading of metrics."""
    file_path = temp_data_dir / "results" / "run_sequential_0" / "final_metrics.json"
    metrics = load_single_run_metrics(file_path)
    assert metrics['total_rule_evaluations'] == 1000
    assert metrics['condition'] == 'sequential'

def test_load_single_run_metrics_not_found():
    """Test error handling for missing file."""
    with pytest.raises(ParityVerificationError):
        load_single_run_metrics(Path("nonexistent/file.json"))

def test_extract_evaluation_count_direct(temp_data_dir):
    """Test extracting count from direct field."""
    file_path = temp_data_dir / "results" / "run_sequential_0" / "final_metrics.json"
    metrics = load_single_run_metrics(file_path)
    count = extract_evaluation_count(metrics)
    assert count == 1000

def test_extract_condition_from_path(temp_data_dir):
    """Test condition extraction from path."""
    file_path = temp_data_dir / "results" / "run_coevolving_1" / "final_metrics.json"
    condition = extract_condition_from_path(file_path)
    assert condition == 'coevolving'

def test_collect_all_run_metrics(temp_data_dir):
    """Test collecting all metrics from directory."""
    run_files = collect_all_run_metrics(temp_data_dir / "results")
    assert len(run_files) == 9  # 3 conditions * 3 runs
    
    conditions = set(r[2] for r in run_files)
    assert conditions == {'sequential', 'mixed', 'coevolving'}

def test_generate_parity_report_success(temp_data_dir):
    """Test successful parity report generation."""
    report = generate_parity_report(temp_data_dir / "results", expected_budget=1000)
    
    assert report.total_runs == 9
    assert report.runs_with_violations == 0
    assert report.all_conditions_meet_parity
    assert report.verification_passed
    assert report.expected_budget == 1000

def test_generate_parity_report_violations(temp_data_dir):
    """Test report generation with parity violations."""
    # Modify one run to exceed budget
    run_dir = temp_data_dir / "results" / "run_sequential_0"
    metrics = {"total_rule_evaluations": 1005, "condition": "sequential"}
    with open(run_dir / "final_metrics.json", 'w') as f:
        json.dump(metrics, f)
    
    report = generate_parity_report(temp_data_dir / "results", expected_budget=1000)
    
    assert report.runs_with_violations == 1
    assert not report.all_conditions_meet_parity
    assert not report.verification_passed

def test_save_parity_report(temp_data_dir):
    """Test saving the parity report."""
    output_path = temp_data_dir / "parity_report.json"
    report = generate_parity_report(temp_data_dir / "results", expected_budget=1000)
    save_parity_report(report, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'summary' in data
    assert data['summary']['total_runs'] == 9
    assert 'details' in data
    assert len(data['details']) == 9