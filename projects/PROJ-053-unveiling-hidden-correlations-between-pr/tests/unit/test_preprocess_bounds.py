import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np

# Mock config for testing if real config is not available in test env
# But per instructions, we assume config is set up. 
# We will test the logic directly by importing functions.

def test_save_normalization_bounds_structure():
    """Test that normalization_bounds.json has the correct structure."""
    from code.data.preprocess import save_normalization_bounds
    
    bounds = {
        "laser_power": {"min": 100.0, "max": 400.0},
        "scan_speed": {"min": 200.0, "max": 1000.0},
        "layer_thickness": {"min": 0.03, "max": 0.05}
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "bounds.json")
        save_normalization_bounds(bounds, path, None)
        
        assert os.path.exists(path)
        with open(path, 'r') as f:
            data = json.load(f)
        
        assert "laser_power" in data
        assert "scan_speed" in data
        assert "layer_thickness" in data
        assert data["laser_power"]["min"] == 100.0
        assert data["laser_power"]["max"] == 400.0

def test_bounds_from_real_split():
    """Test that bounds are correctly calculated from a mock train set."""
    from code.data.preprocess import split_and_scale
    
    # Create mock data
    np.random.seed(42)
    data = {
        'laser_power': np.random.uniform(100, 400, 100),
        'scan_speed': np.random.uniform(200, 1000, 100),
        'layer_thickness': np.random.uniform(0.03, 0.05, 100),
        'yield_strength': np.random.uniform(300, 600, 100),
        'ductility': np.random.uniform(10, 30, 100)
    }
    df = pd.DataFrame(data)
    
    feature_cols = ['laser_power', 'scan_speed', 'layer_thickness']
    target_cols = ['yield_strength', 'ductility']
    
    # Mock logger
    class MockLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass
    
    train_df, test_df, bounds = split_and_scale(df, feature_cols, target_cols, 42, MockLogger())
    
    # Verify bounds match the train set
    for col in feature_cols:
        assert abs(bounds[col]["min"] - train_df[col].min()) < 1e-6
        assert abs(bounds[col]["max"] - train_df[col].max()) < 1e-6
        
        # Verify scaled values are in [0, 1]
        assert train_df[col].min() >= 0.0
        assert train_df[col].max() <= 1.0

def test_missing_feature_handling():
    """Test behavior when a numeric feature is missing from data."""
    from code.data.preprocess import split_and_scale
    
    data = {
        'laser_power': [100, 200, 300],
        'scan_speed': [200, 300, 400],
        # layer_thickness missing
        'yield_strength': [300, 400, 500],
        'ductility': [10, 15, 20]
    }
    df = pd.DataFrame(data)
    
    feature_cols = ['laser_power', 'scan_speed', 'layer_thickness']
    target_cols = ['yield_strength', 'ductility']
    
    class MockLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass
    
    # Should raise KeyError if column missing
    with pytest.raises(KeyError):
        split_and_scale(df, feature_cols, target_cols, 42, MockLogger())
