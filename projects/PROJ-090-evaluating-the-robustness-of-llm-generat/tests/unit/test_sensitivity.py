import pytest
import pandas as pd
import json
from pathlib import Path
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.analysis.statistics import run_sensitivity_analysis, save_sensitivity_report, SensitivityAnalysisResult

@pytest.fixture
def mock_data(tmp_path):
    """Create mock data files for testing."""
    # Create directories
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    # Mock perturbation candidates
    candidates = [
        {"task_id": "1", "perturbation_type": "synonym", "raw_score": 0.96, "perturbation_id": "p1"},
        {"task_id": "1", "perturbation_type": "synonym", "raw_score": 0.88, "perturbation_id": "p2"},
        {"task_id": "2", "perturbation_type": "typo", "raw_score": 0.97, "perturbation_id": "p3"},
        {"task_id": "2", "perturbation_type": "typo", "raw_score": 0.84, "perturbation_id": "p4"},
    ]
    candidates_path = data_dir / "perturbation_candidates_raw.json"
    with open(candidates_path, 'w') as f:
        json.dump(candidates, f)
    
    # Mock execution results
    # Assuming 1:1 mapping with candidates for simplicity in this test
    # perturbed_pass: 1 for pass, 0 for fail
    exec_results = [
        {"task_id": "1", "perturbation_id": "p1", "perturbed_pass": 1},
        {"task_id": "1", "perturbation_id": "p2", "perturbed_pass": 0},
        {"task_id": "2", "perturbation_id": "p3", "perturbed_pass": 1},
        {"task_id": "2", "perturbation_id": "p4", "perturbed_pass": 0},
    ]
    exec_path = data_dir / "execution_results.json"
    with open(exec_path, 'w') as f:
        json.dump(exec_results, f)
    
    return data_dir

def test_sensitivity_analysis_thresholds(mock_data, tmp_path):
    """
    Verify that sensitivity analysis runs and produces the correct thresholds.
    """
    # Change working directory to tmp_path to simulate project root
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        results = run_sensitivity_analysis()
        
        # Verify we have results
        assert len(results) > 0, "No results generated"
        
        # Verify thresholds
        thresholds = sorted(list(set([r.threshold for r in results])))
        expected_thresholds = [0.85, 0.90, 0.95, 0.99]
        assert thresholds == expected_thresholds, f"Expected {expected_thresholds}, got {thresholds}"
        
        # Verify structure
        for r in results:
            assert isinstance(r, SensitivityAnalysisResult)
            assert hasattr(r, 'pass_rate')
            assert hasattr(r, 'delta_from_baseline')
            
    finally:
        os.chdir(original_cwd)

def test_sensitivity_report_csv(mock_data, tmp_path):
    """
    Verify that the CSV report is generated with correct columns and row count.
    """
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        results = run_sensitivity_analysis()
        output_file = tmp_path / "data" / "processed" / "sensitivity_report.csv"
        save_sensitivity_report(results, str(output_file))
        
        # Verify file exists
        assert output_file.exists(), "CSV file not created"
        
        # Verify content
        df = pd.read_csv(output_file)
        assert len(df) == 4, f"Expected 4 rows, got {len(df)}"
        assert set(df['threshold']) == {0.85, 0.90, 0.95, 0.99}, "Thresholds mismatch"
        assert 'pass_rate' in df.columns, "Missing pass_rate column"
        assert 'delta_from_baseline' in df.columns, "Missing delta_from_baseline column"
        
    finally:
        os.chdir(original_cwd)

def test_sensitivity_delta_calculation(mock_data, tmp_path):
    """
    Verify that delta_from_baseline is calculated correctly.
    """
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        results = run_sensitivity_analysis()
        
        # Find the baseline result (0.95)
        baseline_results = [r for r in results if r.threshold == 0.95]
        assert len(baseline_results) > 0, "No baseline results found"
        
        # Verify delta for baseline is 0
        for r in baseline_results:
            assert r.delta_from_baseline == 0.0, f"Baseline delta should be 0, got {r.delta_from_baseline}"
        
    finally:
        os.chdir(original_cwd)
