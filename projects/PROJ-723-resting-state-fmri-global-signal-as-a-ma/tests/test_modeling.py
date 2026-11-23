"""
Unit tests for the modeling module (T019).
"""
import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from modeling import load_cleaned_data, prepare_model_data, run_ridge_regression_with_nested_cv
from utils import write_csv, read_csv, write_json, read_json

def test_load_cleaned_data():
    """Test loading cleaned data."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame({
            'Subject_ID': [1, 2, 3],
            'Global_Signal_SD': [0.5, 0.6, 0.7],
            'MWQ_Score': [10, 20, 30],
            'Age': [25, 30, 35],
            'Sex': [0, 1, 0],
            'Mean_FD': [0.1, 0.2, 0.3],
            'Mean_DVARS': [0.05, 0.06, 0.07]
        })
        df.to_csv(f.name, index=False)
        temp_path = f.name

    try:
        loaded_df = load_cleaned_data(temp_path)
        assert len(loaded_df) == 3
        assert 'Subject_ID' in loaded_df.columns
    finally:
        os.unlink(temp_path)

def test_prepare_model_data():
    """Test feature matrix and target vector preparation."""
    df = pd.DataFrame({
        'Subject_ID': [1, 2, 3],
        'Global_Signal_SD': [0.5, 0.6, 0.7],
        'MWQ_Score': [10, 20, 30],
        'Age': [25, 30, 35],
        'Sex': [0, 1, 0],
        'Mean_FD': [0.1, 0.2, 0.3],
        'Mean_DVARS': [0.05, 0.06, 0.07]
    })

    X, y, subject_ids, feature_names = prepare_model_data(df)
    
    assert X.shape == (3, 5)
    assert y.shape == (3,)
    assert len(subject_ids) == 3
    assert feature_names == ['Global_Signal_SD', 'Mean_FD', 'Mean_DVARS', 'Age', 'Sex']

def test_ridge_regression_with_nested_cv():
    """Test the full nested CV pipeline."""
    # Create synthetic but deterministic data
    np.random.seed(42)
    n = 50
    X = np.random.randn(n, 5)
    y = 2.0 * X[:, 0] + 1.0 * X[:, 1] + np.random.randn(n) * 0.5
    subject_ids = np.arange(n)
    feature_names = ['f1', 'f2', 'f3', 'f4', 'f5']

    results = run_ridge_regression_with_nested_cv(X, y, subject_ids, feature_names, n_splits=3)

    assert 'mae' in results
    assert 'r' in results
    assert 'r_squared' in results
    assert 'alpha' in results
    assert 'residuals' in results
    assert len(results['residuals']) == n
    
    # Check residuals are centered (mean close to 0)
    assert abs(np.mean(results['residuals'])) < 0.1

def test_output_persistence():
    """Test that outputs are written to disk correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Prepare data
        df = pd.DataFrame({
            'Subject_ID': list(range(20)),
            'Global_Signal_SD': np.random.rand(20) * 0.5,
            'MWQ_Score': np.random.rand(20) * 30,
            'Age': np.random.randint(18, 60, 20),
            'Sex': np.random.randint(0, 2, 20),
            'Mean_FD': np.random.rand(20) * 0.3,
            'Mean_DVARS': np.random.rand(20) * 0.1
        })
        
        csv_path = os.path.join(tmpdir, 'test_data.csv')
        df.to_csv(csv_path, index=False)
        
        results_path = os.path.join(tmpdir, 'results.json')
        residuals_path = os.path.join(tmpdir, 'residuals.csv')
        
        # Run pipeline manually
        loaded_df = load_cleaned_data(csv_path)
        X, y, subject_ids, feature_names = prepare_model_data(loaded_df)
        model_results = run_ridge_regression_with_nested_cv(X, y, subject_ids, feature_names, n_splits=2)
        
        # Save results
        write_json(results_path, model_results)
        
        residuals_df = pd.DataFrame({
            'Subject_ID': model_results['subject_ids'],
            'residual_value': model_results['residuals']
        })
        write_csv(residuals_path, residuals_df)
        
        # Verify files exist and content
        assert os.path.exists(results_path)
        assert os.path.exists(residuals_path)
        
        saved_results = read_json(results_path)
        assert saved_results['mae'] is not None
        
        saved_residuals = read_csv(residuals_path)
        assert 'Subject_ID' in saved_residuals.columns
        assert 'residual_value' in saved_residuals.columns
        assert len(saved_residuals) == 20

if __name__ == '__main__':
    test_load_cleaned_data()
    test_prepare_model_data()
    test_ridge_regression_with_nested_cv()
    test_output_persistence()
    print("All tests passed.")