import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path

# Import the module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from features.collinearity import calculate_vif, get_collinear_features, save_vif_report

@pytest.fixture
def sample_data():
    """Create a sample dataframe with known collinearity."""
    np.random.seed(42)
    n = 100
    # Create correlated features
    x1 = np.random.normal(0, 1, n)
    x2 = x1 * 0.9 + np.random.normal(0, 0.1, n)  # Highly correlated with x1
    x3 = np.random.normal(0, 1, n)  # Independent
    return pd.DataFrame({'x1': x1, 'x2': x2, 'x3': x3})

def test_calculate_vif(sample_data):
    """Test VIF calculation returns expected structure."""
    vif_scores = calculate_vif(sample_data, ['x1', 'x2', 'x3'])
    
    assert isinstance(vif_scores, dict)
    assert set(vif_scores.keys()) == {'x1', 'x2', 'x3'}
    assert all(isinstance(v, (int, float, np.floating)) for v in vif_scores.values())
    
    # x1 and x2 should have high VIF due to correlation
    assert vif_scores['x1'] > 1.0
    assert vif_scores['x2'] > 1.0
    # x3 should have low VIF
    assert vif_scores['x3'] < 2.0

def test_get_collinear_features(sample_data):
    """Test collinearity detection."""
    vif_scores = calculate_vif(sample_data, ['x1', 'x2', 'x3'])
    
    # Default threshold is typically 5
    collinear = get_collinear_features(vif_scores, threshold=5.0)
    
    assert isinstance(collinear, list)
    # With high correlation (0.9), VIF should be > 5
    # VIF = 1 / (1 - R^2). If R^2 ~ 0.81, VIF ~ 5.26
    assert 'x1' in collinear or 'x2' in collinear

def test_save_vif_report(sample_data):
    """Test saving VIF report to YAML."""
    vif_scores = calculate_vif(sample_data, ['x1', 'x2', 'x3'])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "vif_report.yaml"
        save_vif_report(vif_scores, output_path)
        
        assert output_path.exists()
        
        # Verify file is readable YAML
        import yaml
        with open(output_path, 'r') as f:
            report = yaml.safe_load(f)
        
        assert 'vif_threshold' in report
        assert 'predictors' in report
        assert len(report['predictors']) == 3
        
        for pred in report['predictors']:
            assert 'feature_name' in pred
            assert 'vif_score' in pred
            assert 'is_collinear' in pred
            assert isinstance(pred['is_collinear'], bool)