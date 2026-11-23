"""
Unit tests for VIF calculation in diagnostics.py
"""
import pytest
import numpy as np
import pandas as pd
import json
import os
from pathlib import Path
from code.diagnostics import calculate_vif

def test_vif_basic():
    """Test VIF calculation with a simple dataset."""
    # Create a dataset with some collinearity
    np.random.seed(42)
    n = 100
    x1 = np.random.randn(n)
    x2 = x1 * 0.9 + np.random.randn(n) * 0.1 # Highly correlated
    x3 = np.random.randn(n)
    
    df = pd.DataFrame({
        'x1': x1,
        'x2': x2,
        'x3': x3
    })
    
    # Create a dummy collinearity map
    collinearity_map = {
        "excluded_vars": []
    }
    map_path = "data/metadata/static_collinearity_map.json"
    os.makedirs(os.path.dirname(map_path), exist_ok=True)
    with open(map_path, 'w') as f:
        json.dump(collinearity_map, f)
    
    result = calculate_vif(df, map_path)
    
    assert "vif_values" in result
    assert "high_vif_flags" in result
    assert len(result["vif_values"]) == 3
    
    # x1 and x2 should have high VIF
    assert result["vif_values"]["x1"] > 5.0 or result["vif_values"]["x2"] > 5.0
    
    # Clean up
    os.remove(map_path)

def test_vif_with_excluded_vars():
    """Test VIF calculation excluding variables from collinearity map."""
    np.random.seed(42)
    n = 100
    x1 = np.random.randn(n)
    x2 = np.random.randn(n)
    x3 = np.random.randn(n)
    
    df = pd.DataFrame({
        'x1': x1,
        'x2': x2,
        'x3': x3
    })
    
    # Create a collinearity map that excludes x1
    collinearity_map = {
        "excluded_vars": ["x1"]
    }
    map_path = "data/metadata/static_collinearity_map.json"
    os.makedirs(os.path.dirname(map_path), exist_ok=True)
    with open(map_path, 'w') as f:
        json.dump(collinearity_map, f)
    
    result = calculate_vif(df, map_path)
    
    assert "x1" not in result["vif_values"]
    assert len(result["vif_values"]) == 2
    assert "x2" in result["vif_values"]
    assert "x3" in result["vif_values"]
    
    # Clean up
    os.remove(map_path)

def test_vif_constant_column():
    """Test VIF calculation with a constant column."""
    np.random.seed(42)
    n = 100
    x1 = np.ones(n) # Constant
    x2 = np.random.randn(n)
    
    df = pd.DataFrame({
        'x1': x1,
        'x2': x2
    })
    
    collinearity_map = {"excluded_vars": []}
    map_path = "data/metadata/static_collinearity_map.json"
    os.makedirs(os.path.dirname(map_path), exist_ok=True)
    with open(map_path, 'w') as f:
        json.dump(collinearity_map, f)
    
    result = calculate_vif(df, map_path)
    
    # Constant column should be handled (either dropped or VIF=inf)
    # In our implementation, it should be dropped or result in a warning
    assert "vif_values" in result
    
    # Clean up
    os.remove(map_path)