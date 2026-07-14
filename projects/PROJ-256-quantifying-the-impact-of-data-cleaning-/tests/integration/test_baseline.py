"""
Integration test for baseline analysis pipeline.
Verifies that baseline analysis produces valid metrics.
"""
import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np

# Import from sibling modules
from code.analysis import run_baseline_analysis
from code.utils import compute_file_checksum

@pytest.fixture
def sample_raw_dir():
    """Create a temporary directory with sample CSV data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a sample dataset with known properties
        # Using real-world-like structure: group (categorical) and continuous values
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            'group': np.random.choice(['A', 'B'], n),
            'value1': np.random.randn(n),
            'value2': np.random.randn(n) * 2 + 10
        })
        
        filepath = os.path.join(tmpdir, 'sample_data.csv')
        df.to_csv(filepath, index=False)
        yield tmpdir

def test_baseline_analysis_produces_valid_metrics(sample_raw_dir):
    """
    Verify baseline analysis script produces baseline_metrics.json 
    with valid p-values (0 < p < 1) and finite CIs.
    """
    output_file = os.path.join(sample_raw_dir, 'baseline_metrics.json')
    
    # Run baseline analysis
    result = run_baseline_analysis(sample_raw_dir, output_file=output_file, config={})
    
    assert result['success'], f"Baseline analysis failed: {result.get('error')}"
    assert os.path.exists(output_file), "Output file was not created"
    
    # Load and validate metrics
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    datasets = data.get('datasets', [])
    assert len(datasets) > 0, "No datasets in output"
    
    for dataset in datasets:
        # Check t-tests
        for t_test in dataset.get('t_tests', []):
            if t_test.get('valid'):
                p_val = t_test.get('p_value')
                ci_low = t_test.get('ci_low')
                ci_high = t_test.get('ci_high')
                
                assert p_val is not None, "p_value is None"
                assert 0 <= p_val <= 1, f"p-value {p_val} not in [0, 1]"
                assert not np.isnan(p_val), "p-value is NaN"
                
                assert ci_low is not None, "ci_low is None"
                assert not np.isnan(ci_low), "ci_low is NaN"
                assert not np.isinf(ci_low), "ci_low is infinite"
                
                assert ci_high is not None, "ci_high is None"
                assert not np.isnan(ci_high), "ci_high is NaN"
                assert not np.isinf(ci_high), "ci_high is infinite"
        
        # Check regressions
        for reg in dataset.get('regressions', []):
            if reg.get('valid'):
                p_vals = reg.get('p_values', [])
                ci_coef = reg.get('ci_coefficient', [])
                
                for p_val in p_vals:
                    if p_val is not None:
                        assert 0 <= p_val <= 1, f"Regression p-value {p_val} not in [0, 1]"
                        assert not np.isnan(p_val), "Regression p-value is NaN"
                
                for ci_val in ci_coef:
                    if ci_val is not None:
                        assert not np.isnan(ci_val), "CI value is NaN"
                        assert not np.isinf(ci_val), "CI value is infinite"

def test_baseline_analysis_checksums_output(sample_raw_dir):
    """Verify that the output file has a valid checksum."""
    output_file = os.path.join(sample_raw_dir, 'baseline_metrics.json')
    
    result = run_baseline_analysis(sample_raw_dir, output_file=output_file, config={})
    assert result['success']
    
    checksum = compute_file_checksum(output_file)
    assert checksum is not None
    assert len(checksum) == 64  # SHA256 hex length
    assert all(c in '0123456789abcdef' for c in checksum)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])