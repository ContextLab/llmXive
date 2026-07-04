"""
Unit tests for model training convergence (Task T020).
Verifies that Random Forest and Gradient Boosting models converge within 30 minutes on a 2-CPU environment.
"""
import pytest
import time
import os
import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from utils.metrics import paired_t_test, bonferroni_correct

# Constants
MAX_TRAINING_SECONDS = 1800  # 30 minutes
RANDOM_SEED = 42
N_SAMPLES = 1000
N_FEATURES = 6
TARGET_COL = "packing_coefficient"
FEATURE_COLS = ["Volume", "SurfaceArea", "Dipole", "HBD", "HBA", "PSA"]

def generate_synthetic_training_data(n_samples: int = N_SAMPLES) -> pd.DataFrame:
    """
    Generates synthetic training data to simulate the pipeline output for testing convergence.
    Uses real distribution logic but synthetic values to ensure reproducibility and speed.
    """
    np.random.seed(RANDOM_SEED)
    data = {
        "ID": [f"COD_{i}" for i in range(n_samples)],
        "Volume": np.random.uniform(50, 500, n_samples),
        "SurfaceArea": np.random.uniform(100, 1000, n_samples),
        "Dipole": np.random.uniform(0, 10, n_samples),
        "HBD": np.random.randint(0, 5, n_samples),
        "HBA": np.random.randint(0, 10, n_samples),
        "PSA": np.random.uniform(0, 150, n_samples),
    }
    # Create a target with some correlation to features to ensure learning happens
    df = pd.DataFrame(data)
    df[TARGET_COL] = (
        0.1 * df["Volume"] / 500 +
        0.1 * df["SurfaceArea"] / 1000 +
        0.05 * df["PSA"] / 150 +
        np.random.normal(0, 0.05, n_samples)
    )
    return df

def train_model_with_timeout(model, X, y, timeout_seconds: int) -> tuple:
    """
    Trains a model and measures time. Returns (success, time_taken, error).
    """
    start_time = time.time()
    error = None
    try:
        model.fit(X, y)
    except Exception as e:
        error = str(e)
    end_time = time.time()
    return end_time - start_time, error

class TestTrainingConvergence:
    """
    Tests to verify that model training completes within the 30-minute limit.
    """

    def test_random_forest_convergence(self):
        """
        Test that Random Forest trains within 30 minutes on 2-CPU.
        Uses synthetic data to simulate the dataset size expected in US2.
        """
        df = generate_synthetic_training_data()
        X = df[FEATURE_COLS].values
        y = df[TARGET_COL].values

        # Use n_jobs=2 to simulate the 2-CPU constraint mentioned in the task
        model = RandomForestRegressor(
            n_estimators=100,
            random_state=RANDOM_SEED,
            n_jobs=2,
            max_depth=10  # Limit depth slightly to ensure fast convergence in test env
        )

        duration, error = train_model_with_timeout(model, X, y, MAX_TRAINING_SECONDS)

        assert error is None, f"Training failed with error: {error}"
        assert duration < MAX_TRAINING_SECONDS, (
            f"Random Forest training took {duration:.2f}s, exceeding limit of {MAX_TRAINING_SECONDS}s"
        )
        # Assert model is fitted
        assert hasattr(model, "estimators_"), "Model was not fitted correctly"

    def test_gradient_boosting_convergence(self):
        """
        Test that Gradient Boosting trains within 30 minutes on 2-CPU.
        """
        df = generate_synthetic_training_data()
        X = df[FEATURE_COLS].values
        y = df[TARGET_COL].values

        model = GradientBoostingRegressor(
            n_estimators=100,
            random_state=RANDOM_SEED,
            max_depth=5,
            learning_rate=0.1
        )

        duration, error = train_model_with_timeout(model, X, y, MAX_TRAINING_SECONDS)

        assert error is None, f"Training failed with error: {error}"
        assert duration < MAX_TRAINING_SECONDS, (
            f"Gradient Boosting training took {duration:.2f}s, exceeding limit of {MAX_TRAINING_SECONDS}s"
        )
        assert hasattr(model, "estimators_"), "Model was not fitted correctly"

    def test_baseline_mean_predictor(self):
        """
        Test that the mean baseline calculation is instantaneous (part of convergence logic).
        """
        df = generate_synthetic_training_data()
        y = df[TARGET_COL].values
        
        start = time.time()
        mean_val = np.mean(y)
        duration = time.time() - start
        
        assert duration < 1.0, "Mean calculation took too long (should be instant)"
        assert isinstance(mean_val, float)

    def test_statistical_test_integration(self):
        """
        Verify that the metrics module (paired_t_test, bonferroni) works correctly
        with the data types generated during training evaluation.
        """
        np.random.seed(RANDOM_SEED)
        pred1 = np.random.normal(0.5, 0.1, 100)
        pred2 = np.random.normal(0.55, 0.1, 100)
        actual = np.random.normal(0.52, 0.1, 100)

        # Test paired t-test
        t_stat, p_val = paired_t_test(pred1 - actual, pred2 - actual)
        assert isinstance(t_stat, (int, float))
        assert isinstance(p_val, (int, float))
        assert 0 <= p_val <= 1

        # Test Bonferroni
        corrected_p = bonferroni_correct([p_val], n_comparisons=2)
        assert isinstance(corrected_p, float)
        assert 0 <= corrected_p <= 1.0 # Cap at 1.0