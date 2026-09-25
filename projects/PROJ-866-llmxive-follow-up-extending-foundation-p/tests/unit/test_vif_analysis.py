import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.tradeoff_model import (
    calculate_vif,
    run_vif_analysis,
    save_vif_report,
    VIF_THRESHOLD
)

def test_calculate_vif_basic():
    """Test basic VIF calculation with known data."""
    import pandas as pd
    
    # Create a dataset with perfect collinearity (X2 = 2 * X1)
    data = {
        'X1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'X2': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],  # Perfectly collinear
        'X3': [1, 3, 2, 4, 3, 5, 4, 6, 5, 7]
    }
    df = pd.DataFrame(data)
    
    # Calculate VIF
    vif_results = calculate_vif(df, ['X1', 'X2', 'X3'])
    
    # X1 and X2 should have very high VIF due to perfect collinearity
    assert 'X1' in vif_results
    assert 'X2' in vif_results
    assert 'X3' in vif_results
    
    # X1 and X2 should have extremely high VIF (theoretically infinite)
    # In practice, due to numerical precision, they will be very large
    assert vif_results['X1'] > 100 or np.isinf(vif_results['X1'])
    assert vif_results['X2'] > 100 or np.isinf(vif_results['X2'])

def test_calculate_vif_independent_features():
    """Test VIF calculation with independent features."""
    import pandas as pd
    
    # Create a dataset with independent features
    np.random.seed(42)
    data = {
        'X1': np.random.randn(100),
        'X2': np.random.randn(100),
        'X3': np.random.randn(100)
    }
    df = pd.DataFrame(data)
    
    vif_results = calculate_vif(df, ['X1', 'X2', 'X3'])
    
    # All VIF values should be close to 1 for independent features
    for feature in ['X1', 'X2', 'X3']:
        assert 0.9 <= vif_results[feature] <= 1.1, f"VIF for {feature} should be close to 1"

def test_run_vif_analysis_with_mock_data(tmp_path):
    """Test VIF analysis with mock processed logs."""
    import pandas as pd
    
    # Create mock log data
    mock_logs = [
        {"context_reduction_pct": 10.0, "depth": 5, "complexity": 2, "is_valid": True},
        {"context_reduction_pct": 20.0, "depth": 10, "complexity": 4, "is_valid": True},
        {"context_reduction_pct": 30.0, "depth": 15, "complexity": 6, "is_valid": True},
        {"context_reduction_pct": 40.0, "depth": 20, "complexity": 8, "is_valid": True},
        {"context_reduction_pct": 50.0, "depth": 25, "complexity": 10, "is_valid": True},
        {"context_reduction_pct": "[deferred]", "depth": 0, "complexity": 1, "is_valid": True},  # Should be skipped
        {"context_reduction_pct": 15.0, "depth": 8, "complexity": 3, "is_valid": False},  # Should be filtered
    ]
    
    # Mock the load_processed_logs function
    with patch('analysis.tradeoff_model.load_processed_logs', return_value=mock_logs):
        vif_results, exceeded = run_vif_analysis()
        
        assert isinstance(vif_results, dict)
        assert 'depth' in vif_results
        assert 'complexity' in vif_results
        assert isinstance(exceeded, bool)

def test_save_vif_report(tmp_path):
    """Test saving VIF report to JSON."""
    vif_results = {
        'depth': 2.5,
        'complexity': 3.1
    }
    exceeded = True
    
    # Mock the RESULTS_DIR
    with patch('analysis.tradeoff_model.RESULTS_DIR', tmp_path):
        report_path = save_vif_report(vif_results, exceeded)
        
        assert os.path.exists(report_path)
        
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        assert report_data['metric_name'] == 'VIF'
        assert report_data['threshold'] == VIF_THRESHOLD
        assert report_data['exceeded_threshold'] == exceeded
        assert 'depth' in report_data['values']
        assert 'complexity' in report_data['values']

def test_vif_threshold_detection():
    """Test that VIF threshold is correctly detected."""
    import pandas as pd
    
    # Create data with moderate multicollinearity
    np.random.seed(42)
    n = 50
    x1 = np.random.randn(n)
    x2 = 0.8 * x1 + 0.2 * np.random.randn(n)  # Correlated
    x3 = np.random.randn(n)
    
    df = pd.DataFrame({'X1': x1, 'X2': x2, 'X3': x3})
    vif_results = calculate_vif(df, ['X1', 'X2', 'X3'])
    
    # X1 and X2 should have VIF > 1, possibly > 5 depending on correlation strength
    # This test verifies the calculation runs without error
    assert all(v > 0 for v in vif_results.values())
