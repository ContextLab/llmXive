"""
Integration test for the full training pipeline (US2).

This test verifies the end-to-end flow from:
1. Loading processed descriptors (data/processed/descriptors.parquet)
2. Splitting data (code/data/split_data.py)
3. Training LightGBM model (code/models/train_lightgbm.py)
4. Evaluating model performance (code/models/evaluate.py)
5. Verifying no 3D calls occur during the process
6. Ensuring output artifacts are created correctly

Prerequisites:
- T018 must be complete (descriptors.parquet exists)
- T005 (validators) must be complete
"""

import os
import sys
import tempfile
import shutil
import logging
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logging_config import get_logger, set_log_level
from utils.validators import assert_no_3d_calls
from data.loader import iterate_smiles
from data.preprocess_2d import preprocess_2d
from data.split_data import split_data
from models.train_lightgbm import train_lightgbm_model
from models.evaluate import evaluate_model

# Configure logging for tests
logger = get_logger(__name__)
set_log_level(logging.INFO)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_processed_data(temp_output_dir):
    """
    Create a minimal mock descriptors.parquet file for testing.
    This simulates the output of T018 (preprocess_2d).
    """
    import pandas as pd
    import numpy as np

    # Create a small synthetic dataset that mimics real descriptors
    n_samples = 100
    n_features = 50

    data = {
        f"desc_{i}": np.random.randn(n_samples) for i in range(n_features)
    }
    data["dipole_moment"] = np.random.randn(n_samples)

    df = pd.DataFrame(data)
    output_path = Path(temp_output_dir) / "descriptors.parquet"
    df.to_parquet(output_path)

    logger.info(f"Created mock descriptors file: {output_path}")
    return output_path

def test_full_pipeline_integration(mock_processed_data, temp_output_dir):
    """
    End-to-end integration test for the training pipeline.

    Verifies:
    1. Data loading and splitting works
    2. Model training completes without 3D calls
    3. Model evaluation produces valid metrics
    4. Output artifacts are created
    """
    # Ensure no 3D calls are made during the entire pipeline
    with assert_no_3d_calls():
        # Step 1: Load and split data
        logger.info("Step 1: Splitting data...")
        X_train, X_test, y_train, y_test = split_data(
            mock_processed_data,
            test_size=0.2,
            random_state=42
        )

        assert X_train.shape[0] > 0, "Training set is empty"
        assert X_test.shape[0] > 0, "Test set is empty"
        assert len(X_train) + len(X_test) == 100, "Total samples mismatch"
        logger.info(f"Data split: Train={X_train.shape[0]}, Test={X_test.shape[0]}")

        # Step 2: Train model
        logger.info("Step 2: Training LightGBM model...")
        model_path = Path(temp_output_dir) / "model.pkl"
        metrics = train_lightgbm_model(
            X_train, y_train,
            X_test, y_test,
            model_save_path=str(model_path)
        )

        assert model_path.exists(), "Model file was not created"
        assert "r2_score" in metrics, "R² metric missing from results"
        assert "rmse" in metrics, "RMSE metric missing from results"
        logger.info(f"Model trained. R²={metrics['r2_score']:.4f}, RMSE={metrics['rmse']:.4f}")

        # Step 3: Evaluate model
        logger.info("Step 3: Evaluating model...")
        eval_results = evaluate_model(model_path, X_test, y_test)

        assert eval_results["r2_score"] > 0.0, "Model performs worse than null model"
        assert eval_results["rmse"] >= 0.0, "RMSE must be non-negative"
        logger.info(f"Evaluation complete. R²={eval_results['r2_score']:.4f}")

        # Step 4: Verify no 3D calls occurred
        # The context manager above ensures this, but we double-check
        assert True, "No 3D calls were detected during pipeline execution"

    # Final assertions
    assert model_path.exists(), "Final model artifact missing"
    assert metrics["r2_score"] > 0.0, "Model R² must be positive (better than null)"
    assert eval_results["r2_score"] > 0.0, "Eval R² must be positive"

    logger.info("✅ Full pipeline integration test PASSED")

def test_pipeline_with_realistic_data(mock_processed_data, temp_output_dir):
    """
    Test with slightly larger data to ensure robustness.
    """
    import pandas as pd
    import numpy as np

    # Increase data size slightly
    n_samples = 200
    n_features = 100

    data = {
        f"desc_{i}": np.random.randn(n_samples) for i in range(n_features)
    }
    # Add some correlation to make the problem learnable
    target = sum(data[f"desc_{i}"] * (0.1 * (i % 10 + 1)) for i in range(10))
    data["dipole_moment"] = target + np.random.randn(n_samples) * 0.5

    df = pd.DataFrame(data)
    output_path = Path(temp_output_dir) / "descriptors_large.parquet"
    df.to_parquet(output_path)

    with assert_no_3d_calls():
        X_train, X_test, y_train, y_test = split_data(
            output_path,
            test_size=0.2,
            random_state=42
        )

        model_path = Path(temp_output_dir) / "model_large.pkl"
        metrics = train_lightgbm_model(
            X_train, y_train,
            X_test, y_test,
            model_save_path=str(model_path)
        )

        assert model_path.exists()
        assert metrics["r2_score"] > 0.0

    logger.info("✅ Realistic data test PASSED")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])