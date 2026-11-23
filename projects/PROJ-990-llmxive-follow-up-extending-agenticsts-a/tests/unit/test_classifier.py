"""
Unit tests for classifier proxy validation logic.
"""
import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np

# Mock the config import if needed, or assume it works in test env
# from classifier import validate_proxy_correlation

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_high_correlation_passes(temp_data_dir):
    """Test that high correlation (>0.7) passes validation."""
    holdout_path = os.path.join(temp_data_dir, 'holdout_set.csv')
    labels_path = os.path.join(temp_data_dir, 'utility_labels.csv')
    output_path = os.path.join(temp_data_dir, 'report.json')
    
    # Create data with high correlation
    n = 100
    x = np.random.rand(n) * 100
    y = x + np.random.normal(0, 1, n) # Strong positive correlation
    
    df_holdout = pd.DataFrame({
        'trajectory_id': range(n),
        'turn_id': range(n),
        'entropy': x
    })
    
    df_labels = pd.DataFrame({
        'trajectory_id': range(n),
        'turn_id': range(n),
        'utility_score': y
    })
    
    df_holdout.to_csv(holdout_path, index=False)
    df_labels.to_csv(labels_path, index=False)
    
    # Import inside test to ensure path resolution if needed, 
    # but assuming standard import works.
    from classifier import validate_proxy_correlation
    
    result = validate_proxy_correlation(
        holdout_path=holdout_path,
        utility_labels_path=labels_path,
        output_path=output_path,
        threshold=0.7
    )
    
    assert result['passed'] is True
    assert result['pearson_r'] >= 0.7
    
    # Verify file creation
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        data = json.load(f)
    assert data['passed'] is True

def test_low_correlation_raises(temp_data_dir):
    """Test that low correlation (<0.7) raises an exception."""
    holdout_path = os.path.join(temp_data_dir, 'holdout_set.csv')
    labels_path = os.path.join(temp_data_dir, 'utility_labels.csv')
    output_path = os.path.join(temp_data_dir, 'report.json')
    
    # Create data with low correlation
    n = 100
    x = np.random.rand(n) * 100
    y = np.random.rand(n) * 100 # Random noise, low correlation
    
    df_holdout = pd.DataFrame({
        'trajectory_id': range(n),
        'turn_id': range(n),
        'entropy': x
    })
    
    df_labels = pd.DataFrame({
        'trajectory_id': range(n),
        'turn_id': range(n),
        'utility_score': y
    })
    
    df_holdout.to_csv(holdout_path, index=False)
    df_labels.to_csv(labels_path, index=False)
    
    from classifier import validate_proxy_correlation
    
    with pytest.raises(RuntimeError, match="Proxy validation FAILED"):
        validate_proxy_correlation(
            holdout_path=holdout_path,
            utility_labels_path=labels_path,
            output_path=output_path,
            threshold=0.7
        )