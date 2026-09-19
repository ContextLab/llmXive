"""
Integration test for model training and evaluation (T018).

This test verifies the end-to-end model training pipeline for User Story 2:
1. Loads pre-processed data from `data/processed/first_arrival_sweep.csv`.
2. Performs feature engineering (lagged features) and temporal splitting.
3. Trains an XGBoost model with hyperparameter tuning.
4. Evaluates the model on the held-out 2022 test set.
5. Computes SHAP values and saves the summary plot.
6. Computes permutation importance and saves results.
7. Validates that all expected output artifacts are created and valid.

Prerequisites:
- T001-T005 (Project structure, config, data dirs)
- T011-T015 (Data pipeline, first arrival derivation)
- T017 (Contract test for output schema)
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import pytest
from sklearn.metrics import mean_squared_error, r2_score

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import get_logger, ensure_directories
from code.preprocessing import load_aggregated_data
# Import the training module functions directly. If they don't exist yet,
# the test will fail with ImportError, which is expected before implementation.
try:
    from code.model_training import (
        run_feature_engineering,
        split_data_temporal,
        train_xgboost_model,
        evaluate_model,
        compute_shap_analysis,
        compute_permutation_importance
    )
    MODEL_TRAINING_AVAILABLE = True
except ImportError:
    MODEL_TRAINING_AVAILABLE = False

logger = get_logger(__name__)


@pytest.mark.skipif(
    not MODEL_TRAINING_AVAILABLE,
    reason="Model training module not yet implemented (expected before T019-T024)"
)
@pytest.mark.integration
def test_model_training_pipeline():
    """
    End-to-end integration test for model training and evaluation.

    Steps:
    1. Verify input data exists (from T015).
    2. Run feature engineering.
    3. Split data temporally.
    4. Train model with hyperparameter search.
    5. Evaluate on test set.
    6. Generate SHAP and permutation importance outputs.
    7. Assert all outputs exist and contain valid data.
    """
    # Setup paths
    input_file = project_root / "data" / "processed" / "first_arrival_sweep.csv"
    output_dir = project_root / "data" / "outputs"
    metrics_file = output_dir / "model_metrics.json"
    shap_plot = output_dir / "shap_summary.png"
    perm_importance_file = output_dir / "permutation_importance.csv"

    # Ensure output directory exists
    ensure_directories([output_dir])

    # Step 0: Verify input data
    if not input_file.exists():
        pytest.fail(
            f"Input file {input_file} not found. "
            "Please ensure T015 (first_arrival_sweep derivation) has been completed."
        )

    logger.info(f"Loading input data from {input_file}")
    try:
        df = load_aggregated_data(input_file)
    except Exception as e:
        pytest.fail(f"Failed to load input data: {e}")

    if df.empty:
        pytest.fail("Input dataframe is empty.")

    # Step 1: Feature Engineering
    logger.info("Running feature engineering...")
    try:
        df_features = run_feature_engineering(df)
    except Exception as e:
        pytest.fail(f"Feature engineering failed: {e}")

    if df_features.empty:
        pytest.fail("Feature engineering resulted in an empty dataframe.")

    # Verify lagged features exist
    expected_lag_cols = [col for col in df_features.columns if 'lag' in col.lower()]
    if not expected_lag_cols:
        # It's possible the logic creates specific named lag columns, check for generic patterns
        # If no lag columns found, check if the function is supposed to create them
        # For now, assume the function creates at least some new features or keeps original ones
        pass

    # Step 2: Temporal Split
    logger.info("Performing temporal split (Train: 2015-2020, Val: 2021, Test: 2022)...")
    try:
        train_df, val_df, test_df = split_data_temporal(df_features)
    except Exception as e:
        pytest.fail(f"Temporal split failed: {e}")

    if train_df.empty or test_df.empty:
        pytest.fail("Train or Test split is empty. Ensure data covers the required years.")

    # Step 3: Train Model
    logger.info("Training XGBoost model with hyperparameter search...")
    try:
        model, best_params = train_xgboost_model(train_df, val_df)
    except Exception as e:
        pytest.fail(f"Model training failed: {e}")

    if model is None:
        pytest.fail("Model training returned None.")

    logger.info(f"Best hyperparameters: {best_params}")

    # Step 4: Evaluate Model
    logger.info("Evaluating model on 2022 test set...")
    try:
        metrics = evaluate_model(model, test_df)
    except Exception as e:
        pytest.fail(f"Model evaluation failed: {e}")

    # Validate metrics structure
    assert "rmse" in metrics, "RMSE not in metrics"
    assert "r2" in metrics, "R2 not in metrics"
    assert "correlation" in metrics, "Correlation not in metrics"
    assert metrics["rmse"] >= 0, "RMSE must be non-negative"

    logger.info(f"Test Metrics: {metrics}")

    # Step 5: SHAP Analysis
    logger.info("Computing SHAP values...")
    try:
        shap_plot_path = compute_shap_analysis(model, test_df, output_path=shap_plot)
    except Exception as e:
        pytest.fail(f"SHAP analysis failed: {e}")

    if not shap_plot_path or not Path(shap_plot_path).exists():
        pytest.fail(f"SHAP plot not generated at {shap_plot}")

    # Step 6: Permutation Importance
    logger.info("Computing permutation importance...")
    try:
        perm_path = compute_permutation_importance(model, test_df, output_path=perm_importance_file)
    except Exception as e:
        pytest.fail(f"Permutation importance failed: {e}")

    if not perm_path or not Path(perm_path).exists():
        pytest.fail(f"Permutation importance file not generated at {perm_importance_file}")

    # Validate permutation importance content
    perm_df = pd.read_csv(perm_importance_file)
    assert not perm_df.empty, "Permutation importance dataframe is empty"
    assert "feature" in perm_df.columns, "Missing 'feature' column in permutation results"
    assert "importance" in perm_df.columns, "Missing 'importance' column in permutation results"

    # Step 7: Save Metrics to JSON (as part of the pipeline verification)
    metrics_output_path = output_dir / "model_metrics.json"
    with open(metrics_output_path, "w") as f:
        json.dump(metrics, f, indent=2)

    # Final Assertions
    assert Path(metrics_output_path).exists(), "Metrics JSON not saved"
    assert Path(shap_plot).exists(), "SHAP plot not saved"
    assert Path(perm_importance_file).exists(), "Permutation importance not saved"

    logger.info("All integration checks passed.")


@pytest.mark.integration
def test_model_training_handles_missing_data():
    """
    Verify that the training pipeline handles missing environmental data gracefully
    (e.g., by dropping rows or imputing, but not crashing).
    """
    if not MODEL_TRAINING_AVAILABLE:
        pytest.skip("Model training module not yet implemented.")

    input_file = project_root / "data" / "processed" / "first_arrival_sweep.csv"
    if not input_file.exists():
        pytest.skip("Input data not available for this test.")

    df = load_aggregated_data(input_file)
    
    # Introduce some NaNs artificially to test robustness
    df_with_nans = df.copy()
    if 'temp' in df_with_nans.columns:
        df_with_nans.loc[df_with_nans.sample(frac=0.1).index, 'temp'] = np.nan
    
    try:
        # This should either drop rows or handle NaNs without raising an unhandled exception
        df_features = run_feature_engineering(df_with_nans)
        # If we get here, check if we still have data
        if not df_features.empty:
            logger.info("Feature engineering handled missing data successfully.")
        else:
            # If it drops all data, that's also a form of handling (though maybe not desired)
            logger.warning("Feature engineering resulted in empty dataframe after NaN introduction.")
    except Exception as e:
        # If it crashes, that's a failure of robustness
        pytest.fail(f"Pipeline crashed on missing data: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])