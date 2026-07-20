import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path

# Add code to path if running as script
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis import calculate_vif, run_vif_check_and_pca, apply_pca
from code.config import VIF_THRESHOLD

def test_vif_calculation_low_correlation():
    """Test VIF when features are uncorrelated (should be ~1)"""
    np.random.seed(42)
    data = pd.DataFrame({
        'branch_points': np.random.rand(100),
        'total_length': np.random.rand(100),
        'soma_area': np.random.rand(100),
        'sholl_intersections': np.random.rand(100)
    })
    
    vif_scores = calculate_vif(data)
    
    # With random data, VIF should be close to 1
    for feature, vif in vif_scores.items():
        assert 0.9 <= vif <= 1.5, f"VIF for {feature} is {vif}, expected ~1"

def test_vif_calculation_high_correlation():
    """Test VIF when features are highly correlated (should be > 5)"""
    np.random.seed(42)
    base = np.random.rand(100)
    data = pd.DataFrame({
        'branch_points': base,
        'total_length': base * 2 + np.random.rand(100) * 0.1, # Highly correlated
        'soma_area': base * 0.5 + np.random.rand(100) * 0.1,
        'sholl_intersections': np.random.rand(100)
    })
    
    vif_scores = calculate_vif(data)
    
    # branch_points and total_length should have high VIF
    assert vif_scores['branch_points'] > VIF_THRESHOLD, f"Expected high VIF for branch_points, got {vif_scores['branch_points']}"
    assert vif_scores['total_length'] > VIF_THRESHOLD, f"Expected high VIF for total_length, got {vif_scores['total_length']}"

def test_run_vif_check_and_pca_trigger():
    """Test that PCA is triggered when VIF > threshold"""
    np.random.seed(42)
    base = np.random.rand(100)
    data = pd.DataFrame({
        'brain_region': ['Hippocampus'] * 50 + ['Prefrontal Cortex'] * 50,
        'pathology_status': ['Normal'] * 50 + ['Early AD'] * 50,
        'branch_points': base,
        'total_length': base * 2 + np.random.rand(100) * 0.1,
        'soma_area': base * 0.5 + np.random.rand(100) * 0.1,
        'sholl_intersections': np.random.rand(100)
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'input.csv')
        output_path = os.path.join(tmpdir, 'vif_check.json')
        
        data.to_csv(input_path, index=False)
        
        result_df = run_vif_check_and_pca(input_path, output_path, threshold=VIF_THRESHOLD)
        
        # Check JSON output
        with open(output_path, 'r') as f:
            vif_json = json.load(f)
        
        assert vif_json['trigger_pca'] == True
        assert vif_json['max_vif'] > VIF_THRESHOLD
        
        # Check that result_df has PCA columns
        assert 'PC1' in result_df.columns or 'PC2' in result_df.columns

def test_run_vif_check_and_pca_no_trigger():
    """Test that PCA is NOT triggered when VIF < threshold"""
    np.random.seed(42)
    data = pd.DataFrame({
        'brain_region': ['Hippocampus'] * 50 + ['Prefrontal Cortex'] * 50,
        'pathology_status': ['Normal'] * 50 + ['Early AD'] * 50,
        'branch_points': np.random.rand(100),
        'total_length': np.random.rand(100),
        'soma_area': np.random.rand(100),
        'sholl_intersections': np.random.rand(100)
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'input.csv')
        output_path = os.path.join(tmpdir, 'vif_check.json')
        
        data.to_csv(input_path, index=False)
        
        result_df = run_vif_check_and_pca(input_path, output_path, threshold=VIF_THRESHOLD)
        
        with open(output_path, 'r') as f:
            vif_json = json.load(f)
        
        assert vif_json['trigger_pca'] == False
        assert vif_json['max_vif'] <= VIF_THRESHOLD
        
        # Result should be same as input (minus index)
        assert list(result_df.columns) == list(data.columns)