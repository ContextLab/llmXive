import json
import os
import tempfile
from pathlib import Path
import pytest
import sys
from unittest.mock import patch, MagicMock

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.parity_checker import (
    generate_parity_report, 
    save_parity_report, 
    ParityReport, 
    RunParityRecord,
    ParityVerificationError
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        results_dir = root / 'results'
        results_dir.mkdir()
        
        # Create mock run directories
        for i, condition in enumerate(['sequential', 'mixed', 'coevolving']):
            run_dir = results_dir / f'run_{i}_{condition}'
            run_dir.mkdir()
            metrics = {
                'total_rule_evaluations': 1000,
                'accuracy': 0.95,
                'condition': condition
            }
            with open(run_dir / 'final_metrics.json', 'w') as f:
                json.dump(metrics, f)
        
        yield results_dir

def test_generate_parity_report_success(temp_data_dir):
    """Test successful generation of a parity report with no violations."""
    report = generate_parity_report(temp_data_dir, target_budget=1000)
    
    assert report.total_runs == 3
    assert report.runs_passed == 3
    assert report.runs_failed == 0
    assert report.all_parity_verified is True
    assert len(report.violation_details) == 0
    assert report.total_evaluations_aggregate == 3000

def test_generate_parity_report_violations(temp_data_dir):
    """Test generation of a parity report when some runs violate the budget."""
    # Modify one run to exceed the budget
    run_dir = temp_data_dir / 'run_0_sequential'
    metrics = {
        'total_rule_evaluations': 1050, # Violation
        'accuracy': 0.95
    }
    with open(run_dir / 'final_metrics.json', 'w') as f:
        json.dump(metrics, f)
    
    report = generate_parity_report(temp_data_dir, target_budget=1000)
    
    assert report.total_runs == 3
    assert report.runs_passed == 2
    assert report.runs_failed == 1
    assert report.all_parity_verified is False
    assert len(report.violation_details) == 1
    assert report.violation_details[0]['run_id'] == 'run_0_sequential'
    assert report.violation_details[0]['deviation'] == 50

def test_save_parity_report(temp_data_dir):
    """Test saving the parity report to a file."""
    report = generate_parity_report(temp_data_dir, target_budget=1000)
    output_path = temp_data_dir.parent / 'parity_report.json'
    
    save_parity_report(report, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'total_runs' in data
    assert data['total_runs'] == 3
    assert data['all_parity_verified'] is True

def test_extract_condition_from_path():
    """Test extraction of condition name from run directory path."""
    from src.analysis.parity_checker import extract_condition_from_path
    
    # Test various path formats
    test_cases = [
        (Path('data/results/run_1_sequential'), 'sequential'),
        (Path('data/results/run_2_mixed'), 'mixed'),
        (Path('data/results/run_3_coevolving'), 'coevolving'),
        (Path('data/results/run_4_unknown'), 'unknown'),
    ]
    
    for path, expected in test_cases:
        result = extract_condition_from_path(path)
        assert result == expected, f"Expected {expected} for {path}, got {result}"

def test_empty_results_directory():
    """Test behavior when results directory is empty or missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        empty_dir = Path(tmpdir) / 'empty_results'
        empty_dir.mkdir()
        
        report = generate_parity_report(empty_dir, target_budget=1000)
        
        assert report.total_runs == 0
        assert report.all_parity_verified is True
        assert report.run_records == []

def test_missing_metrics_file(temp_data_dir):
    """Test behavior when a run directory is missing final_metrics.json."""
    # Remove metrics file from one run
    run_dir = temp_data_dir / 'run_0_sequential'
    (run_dir / 'final_metrics.json').unlink()
    
    # Should log a warning and skip or handle gracefully
    # Based on implementation, it should skip the run
    report = generate_parity_report(temp_data_dir, target_budget=1000)
    
    # Should have 2 runs instead of 3
    assert report.total_runs == 2
    assert report.runs_passed == 2
    assert report.runs_failed == 0