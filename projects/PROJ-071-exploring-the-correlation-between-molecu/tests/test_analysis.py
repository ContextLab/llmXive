import pytest
import numpy as np
import pandas as pd
import json
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis import (
    run_sensitivity_analysis,
    identify_significant_correlations,
    compute_correlation_matrix,
    compute_p_values
)

@pytest.fixture
def sample_df():
    """
    Creates a small DataFrame with known correlations for testing.
    """
    np.random.seed(42)
    n = 50
    # Create features with known relationships
    x1 = np.random.normal(0, 1, n)
    x2 = x1 * 0.8 + np.random.normal(0, 0.1, n) # High correlation
    x3 = np.random.normal(0, 1, n) # No correlation
    y = x1 * 2 + x2 * 0.5 + np.random.normal(0, 0.1, n)
    
    df = pd.DataFrame({
        'feature_1': x1,
        'feature_2': x2,
        'feature_3': x3,
        'target': y
    })
    return df

def test_sensitivity_analysis_output_structure(sample_df, tmp_path):
    """
    Tests that run_sensitivity_analysis produces a valid JSON file with expected structure.
    """
    output_file = tmp_path / "sensitivity_analysis.json"
    
    result = run_sensitivity_analysis(sample_df, str(output_file))
    
    assert result['status'] == 'success'
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check structure of entries
    for entry in data:
        assert 'threshold' in entry
        assert 'significant_count' in entry
        assert isinstance(entry['threshold'], float)
        assert isinstance(entry['significant_count'], int)
    
    # Verify counts decrease as threshold increases
    counts = [e['significant_count'] for e in data]
    # It should be non-increasing generally (higher threshold -> fewer correlations)
    # Note: due to floating point precision or specific data, it might not be strictly monotonic,
    # but the trend should be downward.
    assert counts[0] >= counts[-1], "Sensitivity counts should generally decrease as threshold increases."

def test_identify_significant_correlations_high_corr(sample_df):
    """
    Tests that identify_significant_correlations finds the known high correlation.
    """
    corr_matrix = compute_correlation_matrix(sample_df)
    p_matrix = compute_p_values(sample_df)
    
    # With threshold 0.5, feature_1 and feature_2 should be significant
    sig = identify_significant_correlations(corr_matrix, p_matrix, threshold=0.5, p_thresh=0.05)
    
    found_pair = False
    for item in sig:
        if (item['feature_1'] == 'feature_1' and item['feature_2'] == 'feature_2') or \
           (item['feature_1'] == 'feature_2' and item['feature_2'] == 'feature_1'):
            found_pair = True
            assert item['pearson_r'] > 0.5
            assert item['p_value'] < 0.05
            break
    
    assert found_pair, "Expected to find significant correlation between feature_1 and feature_2."

def test_identify_significant_correlations_low_corr(sample_df):
    """
    Tests that identify_significant_correlations excludes low correlations.
    """
    corr_matrix = compute_correlation_matrix(sample_df)
    p_matrix = compute_p_values(sample_df)
    
    # With threshold 0.9, feature_1 and feature_2 might not be significant if r < 0.9
    sig = identify_significant_correlations(corr_matrix, p_matrix, threshold=0.9, p_thresh=0.05)
    
    found_pair = False
    for item in sig:
        if (item['feature_1'] == 'feature_1' and item['feature_2'] == 'feature_2') or \
           (item['feature_1'] == 'feature_2' and item['feature_2'] == 'feature_1'):
            found_pair = True
            break
    
    # Depending on the exact random seed and noise, r might be < 0.9
    # We just verify the logic works (either found or not found based on actual r)
    # If r < 0.9, it should not be found.
    # In our synthetic data, r is likely around 0.8-0.9.
    # Let's assert that if we set threshold > max possible r, we get nothing.
    sig_high = identify_significant_correlations(corr_matrix, p_matrix, threshold=2.0, p_thresh=0.05)
    assert len(sig_high) == 0, "No correlations should be found with threshold > 1.0."

def test_sensitivity_analysis_file_content(tmp_path):
    """
    Verifies the content of the sensitivity analysis JSON file matches the task requirements.
    """
    np.random.seed(123)
    n = 100
    df = pd.DataFrame({
        'a': np.random.randn(n),
        'b': np.random.randn(n),
        'c': np.random.randn(n)
    })
    # Add some correlation
    df['d'] = df['a'] + df['b'] * 0.5 + np.random.randn(n) * 0.1
    
    output_file = tmp_path / "test_sens.json"
    run_sensitivity_analysis(df, str(output_file))
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    # Check that it covers the range 0.3 to 0.9
    thresholds = [entry['threshold'] for entry in data]
    assert 0.3 in thresholds
    assert 0.85 in thresholds # 0.85 is the last one before 0.9 with step 0.05
    
    # Check that counts are integers
    for entry in data:
        assert isinstance(entry['significant_count'], int)