"""
Unit tests for VIF calculation logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the function to test
# Assuming the module is code.utils.vif_calculator
# We need to adjust the import path if running from root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.vif_calculator import calculate_vif, run_vif_diagnostic

def test_calculate_vif_basic():
    """Test VIF calculation on a simple dataset with no collinearity."""
    data = pd.DataFrame({
        'f1': [1.0, 2.0, 3.0, 4.0, 5.0],
        'f2': [2.0, 4.0, 6.0, 8.0, 10.0], # Perfectly correlated with f1
        'f3': [1.0, 1.0, 2.0, 2.0, 3.0]  # Independent
    })
    
    # f1 and f2 are perfectly collinear -> VIF should be infinite
    # f3 is independent -> VIF should be close to 1
    
    # Note: The calculate_vif function drops constant columns and handles NaNs.
    # Here, we have perfect collinearity between f1 and f2.
    # The implementation uses np.linalg.lstsq which might handle this or return inf.
    
    vif_results = calculate_vif(data, ['f1', 'f2', 'f3'])
    
    # Check that f1 and f2 have high VIF (inf or very large)
    assert np.isinf(vif_results['f1']) or vif_results['f1'] > 1000, f"f1 VIF should be very high, got {vif_results['f1']}"
    assert np.isinf(vif_results['f2']) or vif_results['f2'] > 1000, f"f2 VIF should be very high, got {vif_results['f2']}"
    
    # f3 should have low VIF
    assert not np.isinf(vif_results['f3']), "f3 VIF should not be infinite"
    assert vif_results['f3'] < 5.0, f"f3 VIF should be low, got {vif_results['f3']}"

def test_calculate_vif_independent():
    """Test VIF on independent features."""
    np.random.seed(42)
    data = pd.DataFrame({
        'f1': np.random.rand(100),
        'f2': np.random.rand(100),
        'f3': np.random.rand(100)
    })
    
    vif_results = calculate_vif(data, ['f1', 'f2', 'f3'])
    
    # For independent features, VIF should be close to 1
    for col in ['f1', 'f2', 'f3']:
        assert not np.isinf(vif_results[col]), f"{col} VIF should not be infinite"
        assert vif_results[col] < 5.0, f"{col} VIF should be low, got {vif_results[col]}"

def test_run_vif_diagnostic_file_io():
    """Test that run_vif_diagnostic reads input and writes output correctly."""
    # Create a temporary input file
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        # Create dummy data
        data = pd.DataFrame({
            'formula': ['ABX3', 'ABX3', 'ABX3'],
            'T_d': [100, 200, 300],
            'feature1': [1.0, 2.0, 3.0],
            'feature2': [2.0, 4.0, 6.0], # Collinear
            'feature3': [1.0, 1.0, 2.0],
            'total_uncertainty': [0.1, 0.2, 0.3],
            'perovskite_family': ['A', 'A', 'A']
        })
        data.to_csv(input_path, index=False)
        
        # Run diagnostic
        report_df = run_vif_diagnostic(input_path, output_path)
        
        # Check output file exists
        assert output_path.exists(), "Output file should be created"
        
        # Check report content
        assert 'descriptor' in report_df.columns
        assert 'vif_value' in report_df.columns
        assert 'flagged' in report_df.columns
        
        # Check specific values (feature1 and feature2 should be flagged)
        assert report_df['flagged'].sum() >= 1, "At least one feature should be flagged"

def test_vif_threshold_flagging():
    """Test that the flagging logic works correctly with the threshold."""
    data = pd.DataFrame({
        'f1': [1.0, 2.0, 3.0, 4.0, 5.0],
        'f2': [2.0, 4.0, 6.0, 8.0, 10.0], # Perfectly correlated
        'f3': [1.0, 1.0, 2.0, 2.0, 3.0]
    })
    
    vif_results = calculate_vif(data, ['f1', 'f2', 'f3'])
    
    # Manually check flagging logic (threshold = 5.0)
    for col, vif in vif_results.items():
        is_flagged = np.isinf(vif) or (not np.isnan(vif) and vif > 5.0)
        if col in ['f1', 'f2']:
            assert is_flagged, f"{col} should be flagged"
        else:
            assert not is_flagged, f"{col} should not be flagged"