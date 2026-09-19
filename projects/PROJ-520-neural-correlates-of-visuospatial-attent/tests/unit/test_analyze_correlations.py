import pytest
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Import the functions to test
from analyze_correlations import (
    load_feature_matrix,
    compute_correlation_matrix,
    compute_variance_inflation_factors,
    run_correlation_analysis
)

@pytest.fixture
def sample_feature_csv(tmp_path):
    """Create a sample features_matrix.csv for testing."""
    data = {
        'epoch_id': range(100),
        'condition': ['active'] * 50 + ['passive'] * 50,
        'P3_alpha': np.random.normal(10, 2, 100),
        'Pz_alpha': np.random.normal(10, 2, 100),
        'P4_alpha': np.random.normal(10, 2, 100),
        'F3_beta': np.random.normal(5, 1, 100),
        'Fz_beta': np.random.normal(5, 1, 100),
        'F4_beta': np.random.normal(5, 1, 100),
    }
    # Introduce some perfect correlation for testing VIF
    data['P4_alpha'] = data['P3_alpha'] * 1.0 + 0.01 # Near perfect
    
    df = pd.DataFrame(data)
    file_path = tmp_path / 'features_matrix.csv'
    df.to_csv(file_path, index=False)
    return str(file_path)

def test_load_feature_matrix(sample_feature_csv):
    df = load_feature_matrix(sample_feature_csv)
    assert len(df) == 100
    assert 'P3_alpha' in df.columns
    assert 'F4_beta' in df.columns

def test_compute_correlation_matrix(sample_feature_csv):
    df = load_feature_matrix(sample_feature_csv)
    targets = ['P3_alpha', 'Pz_alpha', 'P4_alpha']
    
    corr_vals, cols = compute_correlation_matrix(df, targets)
    
    assert corr_vals.shape == (3, 3)
    assert cols == targets
    
    # Diagonal should be 1.0
    assert np.allclose(np.diag(corr_vals), 1.0)

def test_compute_variance_inflation_factors(sample_feature_csv):
    df = load_feature_matrix(sample_feature_csv)
    targets = ['P3_alpha', 'P4_alpha'] # P4 is highly correlated with P3
    
    vif = compute_variance_inflation_factors(df, targets)
    
    assert 'P3_alpha' in vif
    assert 'P4_alpha' in vif
    # Since P4 is almost a copy of P3, VIF should be very high
    assert vif['P4_alpha'] > 10.0

def test_run_correlation_analysis_creates_file(sample_feature_csv, tmp_path):
    output_file = str(tmp_path / 'feature_metadata.json')
    
    result = run_correlation_analysis(sample_feature_csv, output_file)
    
    assert os.path.exists(output_file)
    assert 'correlation_matrix' in result
    assert 'collinearity_report' in result
    assert result['collinearity_report']['interpretation'] is not None
    
    # Verify JSON content
    with open(output_file, 'r') as f:
        data = json.load(f)
        assert 'columns' in data['correlation_matrix']
        assert 'data' in data['correlation_matrix']
        assert 'vif_scores' in data['collinearity_report']