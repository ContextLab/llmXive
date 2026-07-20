import os
import sys
import json
import pytest
from pathlib import Path
import math

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import get_project_root, get_output_path
from code.train import (
    train_linear_baseline, 
    train_xgboost_nested_cv, 
    load_aligned_dataset, 
    stratified_split, 
    save_model
)
from code.evaluate import (
    compute_absolute_errors, 
    run_statistical_test, 
    save_metrics,
    load_test_split_metadata
)


def test_nested_cv_execution():
    """
    Integration test for nested CV flow in T023.
    
    This test verifies that the full nested cross-validation pipeline
    executes correctly end-to-end, including:
    1. Loading the aligned dataset
    2. Splitting into train/test sets
    3. Running nested CV for XGBoost (inner grid search, outer evaluation)
    4. Saving the best model and split metadata
    5. Verifying the outputs are created and valid
    
    It ensures the nested CV logic runs without errors and produces
    the expected artifacts.
    """
    
    # Setup: Ensure we have the aligned dataset
    dataset_path = get_project_root() / "data" / "processed" / "aligned_dataset.csv"
    assert dataset_path.exists(), f"Required dataset not found at {dataset_path}"
    
    # Load and split data
    df = load_aligned_dataset(dataset_path)
    train_df, test_df, feature_cols = stratified_split(df)
    
    # Verify split sizes are reasonable
    assert len(train_df) > 0, "Training set is empty"
    assert len(test_df) > 0, "Test set is empty"
    assert len(feature_cols) > 0, "No feature columns found"
    
    # Train Linear Baseline (T025) - for comparison
    linear_model = train_linear_baseline(train_df, feature_cols)
    assert linear_model is not None, "Linear baseline training failed"
    
    # Train XGBoost with nested CV (T026) - THE CORE TEST
    # This is the main integration point: nested CV must complete successfully
    xgb_model, best_params = train_xgboost_nested_cv(train_df, feature_cols)
    
    # Assertions on the result of nested CV
    assert xgb_model is not None, "XGBoost model is None after nested CV"
    assert best_params is not None, "Best parameters are None after nested CV"
    assert isinstance(best_params, dict), "Best params should be a dictionary"
    
    # Verify best_params contains expected keys from the grid search
    expected_keys = {'max_depth', 'learning_rate', 'n_estimators'}
    actual_keys = set(best_params.keys())
    assert expected_keys.issubset(actual_keys), \
        f"Best params missing expected keys. Expected: {expected_keys}, Got: {actual_keys}"
    
    # Verify parameter values are within the search space defined in T026
    assert best_params['max_depth'] in [3, 5, 7], \
        f"max_depth {best_params['max_depth']} not in search space [3, 5, 7]"
    assert best_params['learning_rate'] in [0.01, 0.1], \
        f"learning_rate {best_params['learning_rate']} not in search space [0.01, 0.1]"
    assert isinstance(best_params['n_estimators'], int) and 1 <= best_params['n_estimators'] <= 200, \
        f"n_estimators {best_params['n_estimators']} not in range [1, 200]"
    
    # Save models (T026 requirement)
    models_dir = get_project_root() / "code" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    linear_path = models_dir / "best_linear.json"
    xgb_path = models_dir / "best_xgboost.json"
    
    save_model(linear_model, linear_path)
    save_model(xgb_model, xgb_path)
    
    # Verify models were saved to disk
    assert linear_path.exists(), "Linear model was not saved"
    assert xgb_path.exists(), "XGBoost model was not saved"
    
    # Save split metadata for downstream tasks
    splits_dir = get_project_root() / "outputs" / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)
    split_metadata_path = splits_dir / "train_test_split.json"
    save_split_metadata(train_df, test_df, feature_cols, split_metadata_path)
    assert split_metadata_path.exists(), "Split metadata was not saved"
    
    # Compute absolute errors (T027) - verify models can predict
    linear_errors, xgb_errors = compute_absolute_errors(
        test_df, linear_model, xgb_model, feature_cols
    )
    
    assert len(linear_errors) == len(test_df), "Linear errors length mismatch"
    assert len(xgb_errors) == len(test_df), "XGBoost errors length mismatch"
    
    # Verify errors are numeric and not NaN
    for err in linear_errors:
        assert isinstance(err, (int, float)) and not math.isnan(err), \
            f"Invalid linear error value: {err}"
    for err in xgb_errors:
        assert isinstance(err, (int, float)) and not math.isnan(err), \
            f"Invalid XGBoost error value: {err}"
    
    # Run statistical test (T028a, T028b) - verify statistical pipeline
    normality_result = run_statistical_test(linear_errors, xgb_errors)
    assert normality_result is not None, "Statistical test failed to produce result"
    assert 'test_type' in normality_result, "Statistical result missing test_type"
    assert 'p_value' in normality_result, "Statistical result missing p_value"
    
    # Save metrics (T029)
    metrics_path = get_project_root() / "outputs" / "metrics.json"
    save_metrics(
        linear_model, xgb_model, 
        linear_errors, xgb_errors,
        normality_result,
        best_params,
        metrics_path
    )
    
    # Verify metrics.json was created and contains expected data
    assert metrics_path.exists(), "metrics.json was not created"
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    # Verify structure
    assert 'xgboost' in metrics, "Missing 'xgboost' section in metrics"
    assert 'linear_baseline' in metrics, "Missing 'linear_baseline' section in metrics"
    assert 'statistical_test' in metrics, "Missing 'statistical_test' section"
    
    # Verify best_params were recorded in metrics
    assert 'best_xgboost_params' in metrics, "Best params not recorded in metrics"
    assert metrics['best_xgboost_params'] == best_params, "Best params mismatch in metrics"
    
    # Print summary for verification
    print("✓ Nested CV execution test passed")
    print(f"  Best XGBoost params: {best_params}")
    print(f"  Linear R²: {metrics['linear_baseline']['R2']:.4f}")
    print(f"  XGBoost R²: {metrics['xgboost']['R2']:.4f}")
    print(f"  Statistical test: {normality_result['test_type']} (p={normality_result['p_value']:.4f})")
    print(f"  Models saved to: {xgb_path}")


if __name__ == "__main__":
    test_nested_cv_execution()