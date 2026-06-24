import sys
import pathlib
import numpy as np
import pandas as pd
import pytest

# Ensure the project's code directory is on the import path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
CODE_ROOT = PROJECT_ROOT / "code"
sys.path.append(str(CODE_ROOT))

from training.train_rf import train_random_forest

@pytest.mark.parametrize("seed", [0, 42])
def test_random_forest_training_pipeline(seed):
    """
    Integration‑style test for the Random Forest training pipeline.

    - Generates a small synthetic dataset (100 samples, 10 features).
    - Trains a RandomForestRegressor via the `train_random_forest` helper.
    - Checks that the returned metrics are present, numeric and non‑negative.
    """
    rng = np.random.default_rng(seed)
    # Synthetic feature matrix
    X = rng.normal(size=(100, 10))
    # Synthetic target (dipole moment) – positive values with some noise
    y = rng.uniform(0.0, 5.0, size=100)

    # Run the training pipeline
    result = train_random_forest(X, y, random_state=seed, n_estimators=10)

    # Basic sanity checks on the result
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "mae" in result and "rmse" in result, "Metrics missing from result"
    mae = result["mae"]
    rmse = result["rmse"]
    # Metrics must be real numbers and non‑negative
    assert isinstance(mae, (float, np.floating)), "MAE should be a float"
    assert isinstance(rmse, (float, np.floating)), "RMSE should be a float"
    assert mae >= 0.0, "MAE cannot be negative"
    assert rmse >= 0.0, "RMSE cannot be negative"
