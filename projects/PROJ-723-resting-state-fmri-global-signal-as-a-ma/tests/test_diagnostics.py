"""
Unit tests for collinearity diagnostics.
"""
import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np

from diagnostics import calculate_vif, calculate_correlation, run_collinearity_diagnostics


def test_calculate_vif_basic():
    """Test VIF calculation on a simple dataset."""
    data = {
        'A': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'B': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],  # Perfectly correlated with A
        'C': [1, 3, 2, 4, 3, 5, 4, 6, 5, 7]
    }
    df = pd.DataFrame(data)
    
    # B is perfectly collinear with A, so VIF should be very high (or infinite)
    vif_results = calculate_vif(df, ['A', 'B', 'C'])
    
    assert 'A' in vif_results
    assert 'B' in vif_results
    assert 'C' in vif_results
    
    # B should have very high VIF due to perfect correlation with A
    assert vif_results['B'] > 100  # Threshold for "very high" in this test


def test_calculate_correlation_basic():
    """Test correlation calculation."""
    data = {
        'X': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'Y': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    }
    df = pd.DataFrame(data)
    
    corr = calculate_correlation(df, 'X', 'Y')
    
    assert corr == 1.0  # Perfect positive correlation


def test_calculate_correlation_negative():
    """Test negative correlation calculation."""
    data = {
        'X': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'Y': [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    }
    df = pd.DataFrame(data)
    
    corr = calculate_correlation(df, 'X', 'Y')
    
    assert corr == -1.0  # Perfect negative correlation


def test_run_collinearity_diagnostics():
    """Test full collinearity diagnostics pipeline."""
    # Create temporary directory and files
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "cleaned_data.csv")
        output_file = os.path.join(tmpdir, "diagnostics.json")
        
        # Create sample data
        data = {
            'Subject_ID': [f'sub-{i:03d}' for i in range(1, 51)],
            'Global_Signal_SD': np.random.uniform(0.5, 2.0, 50),
            'Mean_FD': np.random.uniform(0.05, 0.4, 50),
            'Mean_DVARS': np.random.uniform(0.1, 0.5, 50),
            'Age': np.random.randint(18, 80, 50),
            'Sex': np.random.choice([0, 1], 50)
        }
        df = pd.DataFrame(data)
        df.to_csv(input_file, index=False)
        
        # Run diagnostics
        results = run_collinearity_diagnostics(input_file, output_file)
        
        # Verify output file exists
        assert os.path.exists(output_file)
        
        # Verify results structure
        assert 'vif' in results
        assert 'high_vif_features' in results
        assert 'gs_fd_correlation' in results
        assert 'n_subjects' in results
        assert 'threshold_vif' in results
        assert 'status' in results
        
        # Verify VIF keys
        expected_predictors = ['Global_Signal_SD', 'Mean_FD', 'Mean_DVARS', 'Age', 'Sex']
        for predictor in expected_predictors:
            assert predictor in results['vif']
        
        # Verify n_subjects
        assert results['n_subjects'] == 50
        
        # Verify status is either 'ok' or 'warning'
        assert results['status'] in ['ok', 'warning']
        
        # If high VIF features are detected, they should be in the list
        if results['high_vif_features']:
            for feature in results['high_vif_features']:
                assert feature in expected_predictors
                assert results['vif'][feature] > 5.0


def test_run_collinearity_diagnostics_missing_input():
    """Test that diagnostics fail gracefully when input file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "nonexistent.csv")
        output_file = os.path.join(tmpdir, "diagnostics.json")
        
        with pytest.raises(FileNotFoundError):
            run_collinearity_diagnostics(input_file, output_file)


def test_run_collinearity_diagnostics_missing_columns():
    """Test that diagnostics fail when required columns are missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "cleaned_data.csv")
        output_file = os.path.join(tmpdir, "diagnostics.json")
        
        # Create data with missing columns
        data = {
            'Subject_ID': [f'sub-{i:03d}' for i in range(1, 11)],
            'Global_Signal_SD': np.random.uniform(0.5, 2.0, 10),
            # Missing Mean_FD, Mean_DVARS, Age, Sex
        }
        df = pd.DataFrame(data)
        df.to_csv(input_file, index=False)
        
        with pytest.raises(ValueError, match="Missing required columns"):
            run_collinearity_diagnostics(input_file, output_file)
