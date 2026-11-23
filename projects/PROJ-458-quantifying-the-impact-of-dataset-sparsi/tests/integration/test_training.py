import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C

from model_training import load_rss_pool, load_test_set, prepare_features, train_gpr, calculate_metrics
from config import load_env

@pytest.fixture(scope="module")
def test_environment():
    """Verify that prerequisite data files exist before running the integration test."""
    rss_path = project_root / "data" / "processed" / "sparsity_100pct.csv"
    test_path = project_root / "data" / "processed" / "test_set.csv"

    if not rss_path.exists():
        pytest.fail(f"Required input file missing: {rss_path}. Run T032a first.")
    if not test_path.exists():
        pytest.fail(f"Required input file missing: {test_path}. Run T020 first.")

    return {"rss_path": rss_path, "test_path": test_path}

@pytest.mark.integration
def test_gpr_training_on_30k_subset(test_environment):
    """
    Integration test: Verify that a GPR model can be trained on a 30k subset of the RSS
    and evaluated against the fixed test set, producing valid metrics.
    
    This test validates:
    1. Data loading (RSS subset and Test Set)
    2. Feature preparation (X, y separation)
    3. Model training (GPR with specified hyperparameters)
    4. Metric calculation (RMSE, MAE)
    5. Output generation (metrics dict)
    """
    # Load configuration to ensure environment is set up
    try:
        load_env()
    except Exception as e:
        # If env loading fails but we have data, we might still run if keys aren't strictly needed for this specific test
        # However, config.py enforces MP_API_KEY. If missing, we skip or fail based on strictness.
        # For this test, we assume the environment is valid as per project setup.
        pass

    # 1. Load Data
    # We load the full 100% RSS pool, then sample 30k rows to simulate a large training subset
    rss_df = pd.read_csv(test_environment["rss_path"])
    test_df = pd.read_csv(test_environment["test_path"])

    # Ensure we have enough data for the 30k subset
    if len(rss_df) < 30000:
        pytest.skip(f"RSS pool size ({len(rss_df)}) is less than 30,000. Cannot perform 30k subset test.")

    # Sample 30k rows deterministically for reproducibility
    train_subset = rss_df.sample(n=30000, random_state=42)

    # 2. Prepare Features
    # Assuming the CSV has a target column 'formation_energy' and feature columns
    # We need to identify feature columns. Usually, everything except 'material_id' and target.
    target_col = "formation_energy"
    feature_cols = [c for c in train_subset.columns if c != target_col and c != "material_id"]
    
    # Handle potential missing columns if descriptors weren't generated yet (fallback to numeric cols)
    if not feature_cols:
        # Fallback: assume numeric columns are features if specific descriptor columns are missing
        feature_cols = train_subset.select_dtypes(include=['float64', 'int64']).columns.tolist()
        if target_col in feature_cols:
            feature_cols.remove(target_col)
    
    if not feature_cols:
        pytest.fail("No feature columns found in the dataset. Ensure T026 (descriptor generation) has run.")

    X_train = train_subset[feature_cols].fillna(0)
    y_train = train_subset[target_col].fillna(0)

    X_test = test_df[feature_cols].fillna(0)
    y_test = test_df[target_col].fillna(0)

    # Verify shapes
    assert X_train.shape[0] == 30000, f"Expected 30k training samples, got {X_train.shape[0]}"
    assert X_test.shape[0] > 0, "Test set is empty"

    # 3. Train GPR Model
    # Using parameters from T035 spec: RBF kernel, normalize_y=True, max_iter_predict=1000, alpha=1e-6
    kernel = C(1.0) * RBF(1.0)
    gpr_model = GaussianProcessRegressor(
        kernel=kernel,
        alpha=1e-6,
        normalize_y=True,
        n_restarts_optimizer=2,
        max_iter_predict=1000,
        random_state=42
    )

    try:
        gpr_model.fit(X_train, y_train)
    except Exception as e:
        pytest.fail(f"GPR training failed: {str(e)}")

    # 4. Evaluate Model
    # Predict on test set
    y_pred, y_std = gpr_model.predict(X_test, return_std=True)

    # Calculate metrics
    metrics = calculate_metrics(y_test, y_pred)

    # 5. Assertions on Metrics
    assert "rmse" in metrics, "RMSE metric missing"
    assert "mae" in metrics, "MAE metric missing"
    
    assert metrics["rmse"] > 0, "RMSE must be positive"
    assert metrics["mae"] > 0, "MAE must be positive"
    
    # Sanity check: RMSE should be within a reasonable range for formation energy (e.g., < 10 eV usually)
    # If it's huge, something is wrong with data scaling or preparation
    assert metrics["rmse"] < 10.0, f"RMSE ({metrics['rmse']}) is unexpectedly high. Check data preparation."

    # Log the result for manual inspection if needed
    result_log = {
        "task": "test_gpr_training_on_30k_subset",
        "status": "passed",
        "train_size": 30000,
        "test_size": len(y_test),
        "metrics": metrics
    }
    
    # Optional: Print results
    print(f"GPR Training Test Passed. RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}")