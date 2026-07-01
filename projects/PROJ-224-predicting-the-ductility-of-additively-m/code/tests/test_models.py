"""
Unit Tests for Model Logic including VIF Calculation.

This file implements T021: Unit test for VIF calculation logic.
"""
import pytest
import pandas as pd
import numpy as np
from typing import List, Optional
import sys
from pathlib import Path
import time

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the function we are testing
# We import calculate_vif from the preprocessing module as per T023 implementation
from data.preprocessing import calculate_vif, apply_vif_filtering
from models.xgboost_model import train_xgboost_model

class TestVIFCalculation:
    """Tests for the VIF calculation logic."""

    def test_vif_perfect_multicollinearity(self):
        """
        Test that VIF is infinite (or very large) when perfect multicollinearity exists.
        If X2 = 2 * X1, VIF should be high.
        """
        data = {
            'X1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'X2': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20], # Perfectly collinear
            'X3': [1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
        }
        df = pd.DataFrame(data)
        vifs = calculate_vif(df, ['X1', 'X2', 'X3'])
        
        # X1 and X2 should have infinite VIF
        assert np.isinf(vifs['X1']) or vifs['X1'] > 1000
        assert np.isinf(vifs['X2']) or vifs['X2'] > 1000
        # X3 should have low VIF
        assert vifs['X3'] < 2.0

    def test_vif_independence(self):
        """
        Test that VIF is close to 1.0 for independent variables.
        """
        np.random.seed(42)
        data = {
            'X1': np.random.randn(100),
            'X2': np.random.randn(100),
            'X3': np.random.randn(100)
        }
        df = pd.DataFrame(data)
        vifs = calculate_vif(df, ['X1', 'X2', 'X3'])
        
        # All VIFs should be close to 1.0
        for col in ['X1', 'X2', 'X3']:
            assert 0.9 < vifs[col] < 2.0, f"VIF for {col} is {vifs[col]}, expected ~1.0"

    def test_vif_single_feature(self):
        """
        Test that VIF is 1.0 for a single feature (no other features to correlate with).
        """
        data = {
            'X1': [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        vifs = calculate_vif(df, ['X1'])
        
        assert vifs['X1'] == 1.0

    def test_vif_with_nan(self):
        """
        Test that VIF calculation handles NaNs gracefully (drops rows).
        """
        data = {
            'X1': [1, 2, np.nan, 4, 5],
            'X2': [2, 4, 6, 8, 10]
        }
        df = pd.DataFrame(data)
        # Should not raise an error
        vifs = calculate_vif(df, ['X1', 'X2'])
        assert 'X1' in vifs.index
        assert 'X2' in vifs.index

class TestMixedEffectsConvergenceCheck:
    """Tests for mixed-effects convergence check logic (placeholder for T024)."""

    def test_convergence_flag_logic(self):
        """
        Verify the logic that checks for convergence flags in a mock result.
        """
        # Mock result object
        class MockResult:
            def __init__(self, converged):
                self.converged = converged
                self.missing_fit = not converged
            
        result_converged = MockResult(True)
        result_not_converged = MockResult(False)

        # Logic check
        assert result_converged.converged is True
        assert result_not_converged.converged is False
        
        # Simulate the check that would be done in T024
        if not result_converged.converged:
            assert False, "Should not fail for converged model"
        
        if not result_not_converged.converged:
            pass # Expected to log error and set flag

def test_apply_vif_filtering_logic():
    """
    Integration test for the VIF filtering logic (T023).
    Simulates the scenario where Energy Density is highly correlated with components.
    """
    # Create a dataset where Energy Density is perfectly derived from components
    # E = P / (v * h * t)
    # We will create synthetic data where P, v, h, t are somewhat random, 
    # but E is calculated exactly. This usually leads to high VIF for E if P,v,h,t are included.
    # However, in reality, P, v, h, t are often correlated with each other too.
    # To trigger the FR-005 logic, we need E VIF > 5.
    
    np.random.seed(42)
    n = 100
    
    # Generate base parameters
    P = np.random.uniform(100, 400, n)
    v = np.random.uniform(0.5, 1.5, n)
    h = np.random.uniform(0.05, 0.15, n)
    t = np.random.uniform(0.02, 0.06, n)
    
    # Calculate E exactly
    E = P / (v * h * t)
    
    # Add some noise to E to make it not perfectly collinear in a mathematical sense,
    # but statistically highly correlated.
    E_noisy = E * (1 + np.random.normal(0, 0.01, n))
    
    df = pd.DataFrame({
        'laser_power': P,
        'scan_speed': v,
        'hatch_spacing': h,
        'layer_thickness': t,
        'energy_density': E_noisy,
        'ductility': np.random.uniform(5, 20, n),
        'alloy_family': ['Inconel718'] * n,
        'has_cr': [1]*n, 'has_al': [0]*n, 'has_ti': [0]*n, 'has_co': [0]*n, 'has_mo': [0]*n, 'has_w': [0]*n
    })
    
    # Run the filtering
    filtered_df, final_vif = apply_vif_filtering(df, vif_threshold=5.0)
    
    # Check that the correct columns remain
    expected_cols = ['energy_density', 'ductility', 'alloy_family', 'has_cr', 'has_al', 'has_ti', 'has_co', 'has_mo', 'has_w']
    
    # The filtered df should NOT have the constituent columns if FR-005 triggered
    assert 'laser_power' not in filtered_df.columns
    assert 'scan_speed' not in filtered_df.columns
    assert 'hatch_spacing' not in filtered_df.columns
    assert 'layer_thickness' not in filtered_df.columns
    
    assert 'energy_density' in filtered_df.columns
    
    # Verify final VIF is low
    assert final_vif['energy_density'] <= 5.0
    
    # Verify row count is preserved
    assert len(filtered_df) == n

def test_xgboost_training_time_budget():
    """
    Integration test for model training time budget (T029).
    Verifies that XGBoost training completes within the specified time budget (600s).
    """
    # Create a synthetic dataset similar to what would be in curated_builds.csv
    # but small enough to train quickly for the test
    np.random.seed(42)
    n_samples = 200
    
    # Generate features
    data = {
        'laser_power': np.random.uniform(100, 400, n_samples),
        'scan_speed': np.random.uniform(0.5, 1.5, n_samples),
        'hatch_spacing': np.random.uniform(0.05, 0.15, n_samples),
        'layer_thickness': np.random.uniform(0.02, 0.06, n_samples),
        'energy_density': np.random.uniform(50, 200, n_samples),
        'has_cr': np.random.randint(0, 2, n_samples),
        'has_al': np.random.randint(0, 2, n_samples),
        'has_ti': np.random.randint(0, 2, n_samples),
        'has_co': np.random.randint(0, 2, n_samples),
        'has_mo': np.random.randint(0, 2, n_samples),
        'has_w': np.random.randint(0, 2, n_samples),
        'ductility': np.random.uniform(5, 20, n_samples),
        'alloy_family': np.random.choice(['Inconel718', 'Inconel625', 'Haynes282'], n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Define features and target
    feature_cols = [
        'laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness',
        'energy_density', 'has_cr', 'has_al', 'has_ti', 'has_co', 'has_mo', 'has_w'
    ]
    target_col = 'ductility'
    
    X = df[feature_cols]
    y = df[target_col]
    
    # Time budget in seconds (as specified in T031)
    time_budget = 600
    
    # Record start time
    start_time = time.time()
    
    # Train the model
    # Using a small n_estimators for the test to ensure it runs quickly
    # but the function should handle the budget regardless
    try:
        model, metrics = train_xgboost_model(
            X=X,
            y=y,
            test_size=0.2,
            time_budget=time_budget,
            n_estimators=50,  # Small number for quick test
            max_depth=3,
            learning_rate=0.1
        )
        
        # Record end time
        elapsed_time = time.time() - start_time
        
        # Assert that training completed within budget
        assert elapsed_time <= time_budget, (
            f"Training took {elapsed_time:.2f}s, exceeding budget of {time_budget}s"
        )
        
        # Assert that model and metrics were returned
        assert model is not None, "Model was not returned"
        assert metrics is not None, "Metrics were not returned"
        
        # Verify metrics contain expected keys
        assert 'r2' in metrics, "R2 metric missing from results"
        assert 'mae' in metrics, "MAE metric missing from results"
        assert 'rmse' in metrics, "RMSE metric missing from results"
        
        # Log the actual time for verification
        print(f"Training completed in {elapsed_time:.2f}s (budget: {time_budget}s)")
        
    except Exception as e:
        # If training fails, we still need to check if it was due to timeout
        elapsed_time = time.time() - start_time
        if elapsed_time > time_budget:
            pytest.fail(f"Training exceeded time budget: {elapsed_time:.2f}s > {time_budget}s")
        else:
            # Some other error occurred
            pytest.fail(f"Training failed with error: {str(e)}")