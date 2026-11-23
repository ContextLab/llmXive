import pytest
import pandas as pd
import numpy as np
import os
import json
import tempfile
from pathlib import Path

# Import the function to test
# Assuming the code is in the parent directory or installed
try:
    from analyze import calculate_vif, save_vif_diagnostic_log
except ImportError:
    # Fallback for testing if path is not set
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
    from analyze import calculate_vif, save_vif_diagnostic_log

def test_calculate_vif_basic():
    """Test VIF calculation on a simple dataset with known collinearity."""
    # Create a dataset with one feature perfectly collinear with another
    # X1 = [1, 2, 3, 4, 5]
    # X2 = X1 * 2 (perfect collinearity -> VIF = inf)
    # X3 = random noise
    np.random.seed(42)
    data = {
        'X1': [1.0, 2.0, 3.0, 4.0, 5.0],
        'X2': [2.0, 4.0, 6.0, 8.0, 10.0],  # Perfectly collinear with X1
        'X3': np.random.randn(5)
    }
    df = pd.DataFrame(data)
    
    vif_df = calculate_vif(df)
    
    assert 'feature' in vif_df.columns
    assert 'vif' in vif_df.columns
    assert len(vif_df) == 3
    
    # Find X2's VIF
    x2_row = vif_df[vif_df['feature'] == 'X2']
    assert len(x2_row) == 1
    # Due to floating point, it might be very large or inf
    assert x2_row['vif'].iloc[0] >= 1000.0 or np.isinf(x2_row['vif'].iloc[0])

def test_save_vif_diagnostic_log():
    """Test saving VIF results to JSON with flagging."""
    vif_data = pd.DataFrame([
        {'feature': 'A', 'vif': 1.5},
        {'feature': 'B', 'vif': 6.0},
        {'feature': 'C', 'vif': 4.0}
    ])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'vif_log.json')
        save_vif_diagnostic_log(vif_data, output_path, threshold=5.0)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            log = json.load(f)
        
        assert log['threshold'] == 5.0
        assert log['total_features'] == 3
        assert log['flagged_count'] == 1
        assert 'B' in log['flagged_features']
        
        # Check details
        details = {d['feature']: d['vif'] for d in log['details']}
        assert details['A'] == 1.5
        assert details['B'] == 6.0
        assert details['C'] == 4.0

def test_vif_no_collinearity():
    """Test VIF on orthogonal features (should be close to 1)."""
    np.random.seed(42)
    # Generate orthogonal-ish data
    X1 = np.random.randn(100)
    X2 = np.random.randn(100)
    X3 = np.random.randn(100)
    
    # Ensure they are not correlated
    df = pd.DataFrame({'X1': X1, 'X2': X2, 'X3': X3})
    
    vif_df = calculate_vif(df)
    
    # All VIFs should be close to 1.0
    for _, row in vif_df.iterrows():
        assert 0.9 <= row['vif'] <= 1.1, f"VIF for {row['feature']} is {row['vif']}, expected ~1.0"