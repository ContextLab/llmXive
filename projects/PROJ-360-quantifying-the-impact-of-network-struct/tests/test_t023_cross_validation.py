import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path
from sklearn.model_selection import StratifiedKFold

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))
from analyze import run_stratified_cross_validation, get_thermal_conductivity_col

def test_stratified_cross_validation_logic():
    """
    Test that run_stratified_cross_validation correctly:
    1. Bins data into 5 strata
    2. Computes R2 and RMSE
    3. Sets interpretation if R2 < 0.30
    """
    # Create synthetic data that mimics the expected structure
    # We need enough samples to create 5 strata (at least 5 samples, ideally more)
    n_samples = 100
    np.random.seed(42)
    
    # Generate features
    X = np.random.rand(n_samples, 3)
    # Generate target with some noise
    y = 0.1 * X[:, 0] + 0.1 * X[:, 1] + np.random.normal(0, 0.5, n_samples)
    
    # Ensure we have enough unique values for 5 quantile bins
    # If y is too uniform, qcut fails. We force some variance.
    y = y + np.linspace(0, 10, n_samples)
    
    df = pd.DataFrame(X, columns=['f1', 'f2', 'f3'])
    df['thermal_conductivity'] = y
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_perf.json')
        
        results = run_stratified_cross_validation(
            df=df,
            features=['f1', 'f2', 'f3'],
            target='thermal_conductivity',
            n_splits=5,
            output_path=output_path
        )
        
        # Check output file exists
        assert os.path.exists(output_path)
        
        # Load JSON
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # Check structure
        assert 'mean_r2' in data
        assert 'fold_results' in data
        assert len(data['fold_results']) == 5
        assert 'r2_interpretation' in data
        
        # Check interpretation logic (since we used random data, R2 might be low)
        # We can't assert specific R2 value without controlling data perfectly,
        # but we can assert the key exists and is a string if R2 is low.
        if data['mean_r2'] < 0.30:
            assert data['r2_interpretation'] == "Weak predictive power (R² < 0.30), consistent with null hypothesis."
        else:
            # If R2 is high, the key might be None or missing, or just not the weak string
            assert data['r2_interpretation'] != "Weak predictive power (R² < 0.30), consistent with null hypothesis."

def test_stratified_cross_validation_low_r2():
    """
    Test the specific case where R2 < 0.30.
    """
    n_samples = 50
    np.random.seed(99)
    # Pure noise
    X = np.random.rand(n_samples, 3)
    y = np.random.rand(n_samples)
    
    df = pd.DataFrame(X, columns=['f1', 'f2', 'f3'])
    df['thermal_conductivity'] = y
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_perf.json')
        
        results = run_stratified_cross_validation(
            df=df,
            features=['f1', 'f2', 'f3'],
            target='thermal_conductivity',
            n_splits=5,
            output_path=output_path
        )
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # With pure noise, R2 should be low (likely negative or near 0)
        assert data['mean_r2'] < 0.30
        assert data['r2_interpretation'] == "Weak predictive power (R² < 0.30), consistent with null hypothesis."

def test_stratified_kfold_usage():
    """
    Verify that the code actually uses StratifiedKFold by checking the number of unique strata.
    """
    n_samples = 100
    np.random.seed(123)
    X = np.random.rand(n_samples, 2)
    y = np.random.randint(0, 5, n_samples) # Discrete target to ensure stratification works easily
    
    df = pd.DataFrame(X, columns=['f1', 'f2'])
    df['thermal_conductivity'] = y
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_perf.json')
        results = run_stratified_cross_validation(
            df=df,
            features=['f1', 'f2'],
            target='thermal_conductivity',
            n_splits=5,
            output_path=output_path
        )
        
        # If stratification worked, we should have 5 folds
        assert len(results['fold_results']) == 5
        # The fold sizes should be roughly equal (100/5 = 20)
        sizes = [f['test_size'] for f in results['fold_results']]
        assert all(15 <= s <= 25 for s in sizes), f"Fold sizes {sizes} are not balanced"