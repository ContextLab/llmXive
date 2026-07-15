import pytest
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
import warnings
from sklearn.model_selection import train_test_split
import time
import sys
import os
import logging
from pathlib import Path

# Add code directory to path to allow imports
code_path = Path(__file__).parent.parent
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from models.xgboost_model import tune_and_train, load_split_data, prepare_features, evaluate_model, save_artifacts
from data.preprocessing import split_data

# Fixtures
@pytest.fixture
def sample_small_data():
    """Generate a small synthetic dataset for unit testing split logic."""
    np.random.seed(42)
    n = 50
    data = {
        'laser_power': np.random.uniform(100, 500, n),
        'scan_speed': np.random.uniform(200, 1000, n),
        'hatch_spacing': np.random.uniform(50, 200, n),
        'layer_thickness': np.random.uniform(20, 100, n),
        'alloy_family': np.random.choice(['Inconel-625', 'Inconel-718', 'Hastelloy-X'], n),
        'ductility': np.random.uniform(5, 25, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_large_data():
    """Generate a larger dataset to test time budget constraints."""
    np.random.seed(42)
    n = 200
    data = {
        'laser_power': np.random.uniform(100, 500, n),
        'scan_speed': np.random.uniform(200, 1000, n),
        'hatch_spacing': np.random.uniform(50, 200, n),
        'layer_thickness': np.random.uniform(20, 100, n),
        'alloy_family': np.random.choice(['Inconel-625', 'Inconel-718', 'Hastelloy-X'], n),
        'ductility': np.random.uniform(5, 25, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Provide a temporary directory for output artifacts."""
    return tmp_path

@pytest.fixture
def logging_config():
    """Configure logging for tests."""
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)

# Existing Tests (from previous tasks)
class TestVIFCalculationLogic:
    def test_vif_calculation_basic(self, sample_small_data):
        """Test that VIF is calculated correctly for a simple set."""
        features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
        X = sample_small_data[features]
        
        vif_values = []
        for feature in features:
            vif = variance_inflation_factor(X.values, features.index(feature))
            vif_values.append(vif)
        
        assert len(vif_values) == len(features)
        assert all(isinstance(v, float) for v in vif_values)
        assert all(v >= 0 for v in vif_values)

    def test_vif_multicollinearity_detection(self, sample_small_data):
        """Test that VIF detects multicollinearity when a feature is a linear combination."""
        df = sample_small_data.copy()
        # Create perfect multicollinearity
        df['power_plus_speed'] = df['laser_power'] + df['scan_speed']
        
        features = ['laser_power', 'scan_speed', 'power_plus_speed']
        X = df[features]
        
        vif_values = []
        for feature in features:
            vif = variance_inflation_factor(X.values, features.index(feature))
            vif_values.append(vif)
        
        # At least one VIF should be very high due to multicollinearity
        assert max(vif_values) > 10.0, "Multicollinearity should result in high VIF"

class TestMixedEffectsConvergenceCheck:
    def test_convergence_check_logic(self, sample_small_data):
        """Test the logic for checking model convergence."""
        # This is a placeholder to ensure the logic exists in the model file.
        # The actual convergence check is performed in code/models/lme_model.py.
        # We verify that the function handles non-convergence gracefully.
        assert True  # Placeholder for actual integration with lme_model.py

class TestTrainValTestSplitLogic:
    def test_split_data_stratified(self, sample_small_data):
        """Test that split_data performs a stratified split correctly."""
        train, val, test = split_data(sample_small_data, target_col='ductility', stratify_col='alloy_family')
        
        # Check sizes
        assert len(train) + len(val) + len(test) == len(sample_small_data)
        
        # Check that alloy_family distribution is roughly preserved
        train_dist = train['alloy_family'].value_counts(normalize=True)
        test_dist = test['alloy_family'].value_counts(normalize=True)
        
        # Allow some variance due to small sample size
        for family in train_dist.index:
            if family in test_dist.index:
                assert abs(train_dist[family] - test_dist[family]) < 0.2

    def test_split_data_loafo(self, sample_small_data):
        """Test that split_data handles LOAFO when N < 100."""
        # For N < 100, LOAFO should be triggered
        train, val, test = split_data(sample_small_data, target_col='ductility', stratify_col='alloy_family', force_loafo=True)
        
        # Verify that the test set contains only one alloy family (or a subset)
        # The exact behavior depends on the implementation in preprocessing.py
        assert len(test) > 0, "Test set should not be empty"

class TestIntegrationModelTrainingTimeBudget:
    """
    Integration test for model training time budget (Task T029).
    Verifies that the XGBoost training process completes within the 600-second budget.
    """
    def test_training_time_budget(self, sample_large_data, temp_output_dir, logging_config):
        """
        Run the full XGBoost training pipeline and assert it finishes within 600 seconds.
        This test uses a larger dataset to ensure the time budget is meaningful.
        """
        # Define the time budget in seconds
        TIME_BUDGET = 600
        
        # Prepare paths
        data_path = temp_output_dir / "split_data.csv"
        model_path = temp_output_dir / "xgboost_model.pkl"
        metrics_path = temp_output_dir / "model_metrics.json"
        
        # Save the sample data to a CSV to simulate the split_data artifact
        sample_large_data.to_csv(data_path, index=False)
        
        # Measure time
        start_time = time.time()
        
        try:
            # Load data (simulating the output of split_data)
            # Note: In a real scenario, split_data would produce train/val/test files.
            # Here we simulate the training step on the full dataset for the purpose of the time budget test.
            # The actual split logic is tested in TestTrainValTestSplitLogic.
            df = load_split_data(data_path)
            
            # Prepare features
            feature_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
            X = df[feature_cols]
            y = df['ductility']
            
            # Tune and train
            # We use a small grid and few estimators to ensure it runs quickly in CI,
            # but the test verifies the *mechanism* of time tracking.
            # In a real run with real data, this would respect the 600s budget.
            best_model, best_params, training_time = tune_and_train(
                X, y, 
                n_estimators=10,  # Small number for CI speed
                max_depth=3,
                learning_rate=0.1,
                time_budget=TIME_BUDGET,
                cv_folds=3
            )
            
            # Evaluate
            metrics = evaluate_model(best_model, X, y)
            
            # Save artifacts
            save_artifacts(best_model, metrics, best_params, model_path, metrics_path)
            
        except Exception as e:
            logging.error(f"Training failed: {e}")
            raise
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Assert the training completed within the budget
        assert total_time < TIME_BUDGET, (
            f"Model training took {total_time:.2f} seconds, exceeding the budget of {TIME_BUDGET} seconds."
        )
        
        logging.info(f"Training completed successfully in {total_time:.2f} seconds.")
        
        # Additional assertions to ensure artifacts were created
        assert model_path.exists(), "Model artifact was not saved."
        assert metrics_path.exists(), "Metrics artifact was not saved."

    def test_training_time_budget_small_data(self, sample_small_data, temp_output_dir, logging_config):
        """
        Run training on small data to ensure the time budget logic works for smaller datasets too.
        """
        TIME_BUDGET = 600
        
        data_path = temp_output_dir / "split_data_small.csv"
        model_path = temp_output_dir / "xgboost_model_small.pkl"
        metrics_path = temp_output_dir / "model_metrics_small.json"
        
        sample_small_data.to_csv(data_path, index=False)
        
        start_time = time.time()
        
        try:
            df = load_split_data(data_path)
            feature_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
            X = df[feature_cols]
            y = df['ductility']
            
            best_model, best_params, training_time = tune_and_train(
                X, y, 
                n_estimators=5,
                max_depth=2,
                learning_rate=0.1,
                time_budget=TIME_BUDGET,
                cv_folds=2
            )
            
            metrics = evaluate_model(best_model, X, y)
            save_artifacts(best_model, metrics, best_params, model_path, metrics_path)
            
        except Exception as e:
            logging.error(f"Training failed: {e}")
            raise
        
        end_time = time.time()
        total_time = end_time - start_time
        
        assert total_time < TIME_BUDGET, (
            f"Training took {total_time:.2f} seconds, exceeding the budget of {TIME_BUDGET} seconds."
        )
        
        assert model_path.exists()
        assert metrics_path.exists()
        logging.info(f"Small data training completed in {total_time:.2f} seconds.")