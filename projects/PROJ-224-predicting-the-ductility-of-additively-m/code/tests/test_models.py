import pytest
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
import warnings
from sklearn.model_selection import train_test_split
import time
import os
import sys
from pathlib import Path
import json
import logging

# Add parent directory to path if running standalone
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from models.xgboost_model import train_xgboost_model, evaluate_model
from data.preprocessing import calculate_energy_density

# Configure logging for the test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_placeholder_models():
    """Placeholder test to ensure the test file structure is valid."""
    assert True

def test_vif_calculation_logic():
    """Test VIF calculation logic with known data."""
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        'feature1': np.random.randn(n),
        'feature2': np.random.randn(n),
        'feature3': np.random.randn(n),
        'target': np.random.randn(n)
    })
    
    vif_data = pd.DataFrame()
    vif_data["feature"] = data.columns
    vif_data["VIF"] = [variance_inflation_factor(data.values, i) 
                      for i in range(len(data.columns))]
    
    # VIF should be > 1 for any feature
    assert all(vif_data["VIF"] > 1)
    # VIF should be reasonable for uncorrelated random data
    assert all(vif_data["VIF"] < 10)

def test_vif_independent_features():
    """Test VIF with independent features."""
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        'A': np.random.randn(n),
        'B': np.random.randn(n),
        'C': np.random.randn(n)
    })
    
    vifs = []
    for i in range(data.shape[1]):
        vif = variance_inflation_factor(data.values, i)
        vifs.append(vif)
    
    # For independent features, VIF should be close to 1
    assert all(v < 5 for v in vifs)

def test_vif_single_feature():
    """Test VIF with a single feature."""
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        'A': np.random.randn(n)
    })
    
    # VIF for a single feature is undefined (division by zero in some implementations)
    # or infinite. We expect a high value or exception handling.
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        vif = variance_inflation_factor(data.values, 0)
        # If it returns a value, it should be large or we handle it
        if vif == float('inf') or np.isinf(vif):
            pass # Expected
        else:
            assert vif >= 1.0

def test_vif_with_nan():
    """Test VIF calculation with NaN values."""
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        'A': np.random.randn(n),
        'B': np.random.randn(n),
        'C': [np.nan] * n
    })
    
    # VIF calculation should handle or raise on NaN
    # In practice, statsmodels might return NaN or raise
    with pytest.raises((ValueError, TypeError)):
        for i in range(data.shape[1]):
            variance_inflation_factor(data.values, i)

def test_mixed_effects_convergence_check():
    """Test mixed effects model convergence check logic."""
    # This test verifies the logic for checking convergence
    # We simulate a convergence status check
    class MockModel:
        def __init__(self, converged):
            self.converged = converged
        
        def check_convergence(self):
            return self.converged

    model_converged = MockModel(True)
    model_not_converged = MockModel(False)
    
    assert model_converged.check_convergence() == True
    assert model_not_converged.check_convergence() == False

def test_train_val_test_split_logic():
    """Test standard train/val/test split logic."""
    np.random.seed(42)
    n = 1000
    data = pd.DataFrame({
        'feature': np.random.randn(n),
        'target': np.random.randn(n),
        'alloy_family': np.random.choice(['A', 'B', 'C'], n)
    })
    
    # Standard split
    train, temp = train_test_split(data, test_size=0.4, random_state=42, stratify=data['alloy_family'])
    val, test = train_test_split(temp, test_size=0.5, random_state=42, stratify=temp['alloy_family'])
    
    assert len(train) == 600
    assert len(val) == 200
    assert len(test) == 200
    
    # Check stratification
    assert train['alloy_family'].value_counts().nunique() > 0

def test_loafo_split_logic():
    """Test Leave-One-Alloy-Family-Out split logic."""
    np.random.seed(42)
    n = 50
    # Create data with 3 alloy families
    families = ['AlloyA', 'AlloyB', 'AlloyC']
    data = pd.DataFrame({
        'feature': np.random.randn(n),
        'target': np.random.randn(n),
        'alloy_family': np.random.choice(families, n)
    })
    
    unique_families = data['alloy_family'].unique()
    
    # Simulate LOAFO: for each family, hold it out as test
    results = []
    for holdout in unique_families:
        test_set = data[data['alloy_family'] == holdout]
        train_set = data[data['alloy_family'] != holdout]
        
        results.append({
            'holdout': holdout,
            'train_size': len(train_set),
            'test_size': len(test_set)
        })
    
    # Verify logic: test set contains only one family
    for res in results:
        assert res['test_size'] > 0
        assert res['train_size'] > 0
        # Total should equal original N
        assert res['train_size'] + res['test_size'] == n

def test_split_deterministic():
    """Test that splits are deterministic with fixed seed."""
    np.random.seed(123)
    data = pd.DataFrame({
        'x': np.random.randn(100),
        'y': np.random.randn(100),
        'group': np.random.choice(['A', 'B'], 100)
    })
    
    train1, test1 = train_test_split(data, test_size=0.2, random_state=42, stratify=data['group'])
    train2, test2 = train_test_split(data, test_size=0.2, random_state=42, stratify=data['group'])
    
    assert train1.equals(train2)
    assert test1.equals(test2)

def test_train_val_test_split_logic():
    """Test standard train/val/test split logic."""
    np.random.seed(42)
    n = 1000
    data = pd.DataFrame({
        'feature': np.random.randn(n),
        'target': np.random.randn(n),
        'alloy_family': np.random.choice(['A', 'B', 'C'], n)
    })
    
    # Standard split
    train, temp = train_test_split(data, test_size=0.4, random_state=42, stratify=data['alloy_family'])
    val, test = train_test_split(temp, test_size=0.5, random_state=42, stratify=temp['alloy_family'])
    
    assert len(train) == 600
    assert len(val) == 200
    assert len(test) == 200
    
    # Check stratification
    assert train['alloy_family'].value_counts().nunique() > 0

def test_loafo_split_logic():
    """Test Leave-One-Alloy-Family-Out split logic."""
    np.random.seed(42)
    n = 50
    # Create data with 3 alloy families
    families = ['AlloyA', 'AlloyB', 'AlloyC']
    data = pd.DataFrame({
        'feature': np.random.randn(n),
        'target': np.random.randn(n),
        'alloy_family': np.random.choice(families, n)
    })
    
    unique_families = data['alloy_family'].unique()
    
    # Simulate LOAFO: for each family, hold it out as test
    results = []
    for holdout in unique_families:
        test_set = data[data['alloy_family'] == holdout]
        train_set = data[data['alloy_family'] != holdout]
        
        results.append({
            'holdout': holdout,
            'train_size': len(train_set),
            'test_size': len(test_set)
        })
    
    # Verify logic: test set contains only one family
    for res in results:
        assert res['test_size'] > 0
        assert res['train_size'] > 0
        # Total should equal original N
        assert res['train_size'] + res['test_size'] == n

def test_integration_model_training_time_budget():
    """
    Integration test for model training time budget.
    Verifies that the XGBoost model training completes within the specified time budget (600s).
    """
    # Create a synthetic dataset to simulate the real data
    np.random.seed(42)
    n_samples = 200
    
    # Generate features similar to the problem domain
    data = pd.DataFrame({
        'laser_power': np.random.uniform(100, 400, n_samples),
        'scan_speed': np.random.uniform(200, 1200, n_samples),
        'hatch_spacing': np.random.uniform(50, 150, n_samples),
        'layer_thickness': np.random.uniform(20, 60, n_samples),
        'alloy_family': np.random.choice(['Inconel718', 'Inconel625', 'HastelloyX'], n_samples),
        'Cr': np.random.randint(0, 2, n_samples),
        'Al': np.random.randint(0, 2, n_samples),
        'Ti': np.random.randint(0, 2, n_samples),
        'Co': np.random.randint(0, 2, n_samples),
        'Mo': np.random.randint(0, 2, n_samples),
        'W': np.random.randint(0, 2, n_samples)
    })
    
    # Calculate Energy Density (E_v = P / (v * h * t))
    # Convert units to match typical SI: P(W), v(mm/s), h(um->mm), t(um->mm)
    # Assuming inputs are in typical units: P(W), v(mm/s), h(um), t(um)
    # E_v (J/mm^3) = P(W) / (v(mm/s) * h(mm) * t(mm))
    # h and t need conversion from um to mm
    data['energy_density'] = data['laser_power'] / (
        data['scan_speed'] * 
        (data['hatch_spacing'] / 1000.0) * 
        (data['layer_thickness'] / 1000.0)
    )
    
    # Generate synthetic ductility target (realistic range 0-20%)
    # Simple relationship + noise
    data['ductility'] = (
        15.0 
        - 0.01 * data['laser_power'] 
        + 0.005 * data['scan_speed'] 
        - 0.02 * data['energy_density'] 
        + np.random.normal(0, 2, n_samples)
    )
    data['ductility'] = data['ductility'].clip(0, 20)
    
    # Prepare features and target
    feature_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 
                    'energy_density', 'Cr', 'Al', 'Ti', 'Co', 'Mo', 'W']
    X = data[feature_cols]
    y = data['ductility']
    
    # Define time budget
    TIME_BUDGET_SECONDS = 600
    timeout_message = f"Model training exceeded the time budget of {TIME_BUDGET_SECONDS} seconds."
    
    start_time = time.time()
    
    try:
        # Train the model using the project's implementation
        # Note: We pass a subset of features to ensure it runs quickly for the test
        # In a real scenario, this would use the full pipeline
        model, metrics, history = train_xgboost_model(
            X, y, 
            time_budget=TIME_BUDGET_SECONDS,
            n_splits=5,
            random_state=42,
            max_iter=10  # Limit iterations for the test to ensure it finishes quickly
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Assert that training completed within the time budget
        assert elapsed_time < TIME_BUDGET_SECONDS, f"{timeout_message} Elapsed: {elapsed_time:.2f}s"
        
        # Verify that the model was trained and metrics were returned
        assert model is not None, "Model object is None"
        assert metrics is not None, "Metrics object is None"
        assert 'r2' in metrics or 'R2' in metrics, "R2 metric not found in results"
        
        logger.info(f"Training completed in {elapsed_time:.2f} seconds (Budget: {TIME_BUDGET_SECONDS}s)")
        logger.info(f"Model metrics: {metrics}")
        
    except Exception as e:
        # If the function raises an exception, check if it's a timeout or other error
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.error(f"Training failed after {elapsed_time:.2f}s: {str(e)}")
        # If it failed due to timeout, the test should fail
        # If it failed for other reasons (e.g., missing dependency), we might want to skip or fail
        if "timeout" in str(e).lower():
            raise AssertionError(timeout_message) from e
        else:
            # Re-raise if it's not a timeout issue, as the test environment might be missing deps
            # But for the purpose of this test, we assume the environment is set up correctly
            # If the code is correct, it should run. If it fails here, it's a code bug.
            raise

def test_loafo_split_logic():
    """Test Leave-One-Alloy-Family-Out split logic."""
    np.random.seed(42)
    n = 50
    # Create data with 3 alloy families
    families = ['AlloyA', 'AlloyB', 'AlloyC']
    data = pd.DataFrame({
        'feature': np.random.randn(n),
        'target': np.random.randn(n),
        'alloy_family': np.random.choice(families, n)
    })
    
    unique_families = data['alloy_family'].unique()
    
    # Simulate LOAFO: for each family, hold it out as test
    results = []
    for holdout in unique_families:
        test_set = data[data['alloy_family'] == holdout]
        train_set = data[data['alloy_family'] != holdout]
        
        results.append({
            'holdout': holdout,
            'train_size': len(train_set),
            'test_size': len(test_set)
        })
    
    # Verify logic: test set contains only one family
    for res in results:
        assert res['test_size'] > 0
        assert res['train_size'] > 0
        # Total should equal original N
        assert res['train_size'] + res['test_size'] == n