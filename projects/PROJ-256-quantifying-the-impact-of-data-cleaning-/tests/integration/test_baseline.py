import os
import json
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Import the function to test
from code.analysis import run_baseline_analysis

BASELINE_OUTPUT = "data/processed/baseline_metrics.json"

@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV dataset for testing."""
    data = {
        'group': ['A', 'A', 'B', 'B', 'A', 'B'],
        'value': [1.0, 2.0, 3.0, 4.0, 1.5, 3.5],
        'predictor': [10, 20, 30, 40, 15, 35]
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "test_dataset.csv"
    df.to_csv(csv_path, index=False)
    return str(tmp_path)

def test_baseline_analysis_creates_file(sample_csv):
    """Test that run_baseline_analysis creates the output file."""
    output_file = os.path.join("data", "processed", "test_baseline_output.json")
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    result = run_baseline_analysis(sample_csv, output_file)
    
    assert result is True, "Baseline analysis should return True on success"
    assert os.path.exists(output_file), "Output file should be created"
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert 'datasets' in data
    assert len(data['datasets']) > 0
    
    # Clean up
    if os.path.exists(output_file):
        os.remove(output_file)

def test_baseline_analysis_p_values_valid(sample_csv):
    """Test that generated p-values are in (0, 1)."""
    output_file = os.path.join("data", "processed", "test_pval_output.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    run_baseline_analysis(sample_csv, output_file)
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    for dataset in data['datasets']:
        for t_test in dataset.get('t_tests', []):
            p_val = t_test.get('p_value')
            if p_val is not None:
                assert 0 < p_val < 1, f"P-value {p_val} is not in (0, 1)"
    
    if os.path.exists(output_file):
        os.remove(output_file)

def test_baseline_analysis_ci_finite(sample_csv):
    """Test that confidence intervals are finite numbers."""
    output_file = os.path.join("data", "processed", "test_ci_output.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    run_baseline_analysis(sample_csv, output_file)
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    for dataset in data['datasets']:
        for t_test in dataset.get('t_tests', []):
            ci_low = t_test.get('ci_low')
            ci_high = t_test.get('ci_high')
            if ci_low is not None:
                assert isinstance(ci_low, (int, float)) and not (ci_low != ci_low), "CI low is not finite"
            if ci_high is not None:
                assert isinstance(ci_high, (int, float)) and not (ci_high != ci_high), "CI high is not finite"
    
    if os.path.exists(output_file):
        os.remove(output_file)