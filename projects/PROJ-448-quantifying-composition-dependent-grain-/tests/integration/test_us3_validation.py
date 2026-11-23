"""
Integration test for cross-validation metrics (US3).

This test verifies the full cross-validation pipeline:
1. Loading data for cross-validation
2. Running k-fold cross-validation
3. Calculating per-fold and aggregate metrics
4. Performing transferability checks
5. Detecting overfitting
6. Aggregating all results into a comprehensive report

The test ensures that all components work together correctly
and produce valid, consistent outputs.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np
import pandas as pd

# Import modules under test
from code.models.validation import load_cv_data, run_cross_validation, calculate_cv_metrics, save_cv_results
from code.services.cv_reporter import load_cv_results, calculate_fold_metrics, compute_summary_statistics, save_cv_metrics_report
from code.services.overfitting_detector import load_cv_results as load_overfit_results, detect_overfitting, save_overfitting_report
from code.services.cv_results_aggregator import aggregate_cross_validation_results, load_json_file, save_json_file
from code.config import PROCESSED_PATH


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_cv_data(temp_data_dir):
    """Generate sample cross-validation data for testing."""
    # Create sample data mimicking segregation profiles
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    
    # Generate features (compositions)
    X = np.random.rand(n_samples, n_features)
    # Generate target (segregation energy) with some noise
    y = 0.5 * X[:, 0] + 0.3 * X[:, 1] - 0.2 * X[:, 2] + np.random.normal(0, 0.1, n_samples)
    
    # Save to CSV
    data_path = temp_data_dir / "cv_input_data.csv"
    df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(n_features)])
    df["target"] = y
    df.to_csv(data_path, index=False)
    
    return {
        "data_path": data_path,
        "X": X,
        "y": y
    }


def test_load_cv_data(sample_cv_data):
    """Test loading cross-validation data from CSV."""
    result = load_cv_data(sample_cv_data["data_path"])
    
    assert result is not None
    assert "X" in result
    assert "y" in result
    assert result["X"].shape == sample_cv_data["X"].shape
    assert result["y"].shape == sample_cv_data["y"].shape
    np.testing.assert_array_almost_equal(result["X"], sample_cv_data["X"])
    np.testing.assert_array_almost_equal(result["y"], sample_cv_data["y"])


def test_run_cross_validation(sample_cv_data, temp_data_dir):
    """Test running k-fold cross-validation."""
    # Run CV with 5 folds
    cv_results = run_cross_validation(
        X=sample_cv_data["X"],
        y=sample_cv_data["y"],
        n_folds=5,
        random_state=42
    )
    
    assert cv_results is not None
    assert "fold_scores" in cv_results
    assert "train_scores" in cv_results
    assert "val_scores" in cv_results
    assert len(cv_results["fold_scores"]) == 5
    assert len(cv_results["train_scores"]) == 5
    assert len(cv_results["val_scores"]) == 5
    
    # Verify scores are reasonable
    assert all(0 <= s <= 1 for s in cv_results["fold_scores"])
    assert all(0 <= s <= 1 for s in cv_results["train_scores"])
    assert all(0 <= s <= 1 for s in cv_results["val_scores"])


def test_calculate_cv_metrics(sample_cv_data, temp_data_dir):
    """Test calculating cross-validation metrics."""
    # First run CV
    cv_results = run_cross_validation(
        X=sample_cv_data["X"],
        y=sample_cv_data["y"],
        n_folds=5,
        random_state=42
    )
    
    # Calculate metrics
    metrics = calculate_cv_metrics(cv_results)
    
    assert metrics is not None
    assert "mean_r2" in metrics
    assert "std_r2" in metrics
    assert "mean_mse" in metrics
    assert "std_mse" in metrics
    assert "num_folds" in metrics
    
    # Verify calculations
    assert metrics["mean_r2"] == np.mean(cv_results["fold_scores"])
    assert metrics["std_r2"] == np.std(cv_results["fold_scores"])
    assert metrics["num_folds"] == 5


def test_save_and_load_cv_results(sample_cv_data, temp_data_dir):
    """Test saving and loading cross-validation results."""
    # Run CV and save results
    cv_results = run_cross_validation(
        X=sample_cv_data["X"],
        y=sample_cv_data["y"],
        n_folds=5,
        random_state=42
    )
    
    output_path = temp_data_dir / "cv_results_test.json"
    save_cv_results(cv_results, output_path)
    
    # Load and verify
    loaded_results = load_cv_results(output_path)
    
    assert loaded_results is not None
    assert "fold_scores" in loaded_results
    assert "train_scores" in loaded_results
    assert "val_scores" in loaded_results
    
    # Verify data integrity
    np.testing.assert_array_almost_equal(
        loaded_results["fold_scores"],
        cv_results["fold_scores"]
    )


def test_cv_metrics_report(sample_cv_data, temp_data_dir):
    """Test generating CV metrics report."""
    # Run CV and calculate metrics
    cv_results = run_cross_validation(
        X=sample_cv_data["X"],
        y=sample_cv_data["y"],
        n_folds=5,
        random_state=42
    )
    
    metrics = calculate_cv_metrics(cv_results)
    
    # Save metrics report
    report_path = temp_data_dir / "cv_metrics_report.json"
    save_cv_metrics_report(metrics, report_path)
    
    # Load and verify
    loaded_metrics = load_json_file(report_path)
    
    assert loaded_metrics["mean_r2"] == metrics["mean_r2"]
    assert loaded_metrics["std_r2"] == metrics["std_r2"]
    assert loaded_metrics["mean_mse"] == metrics["mean_mse"]
    assert loaded_metrics["std_mse"] == metrics["std_mse"]


def test_overfitting_detection(sample_cv_data, temp_data_dir):
    """Test overfitting detection logic."""
    # Create a scenario with potential overfitting
    # High training score, lower validation score
    cv_results = {
        "fold_scores": [0.95, 0.92, 0.88, 0.90, 0.85],
        "train_scores": [0.99, 0.98, 0.97, 0.98, 0.96],
        "val_scores": [0.85, 0.82, 0.78, 0.80, 0.75],
        "model_params": {"n_estimators": 100}
    }
    
    # Detect overfitting
    overfit_results = detect_overfitting(cv_results)
    
    assert overfit_results is not None
    assert "is_overfitting" in overfit_results
    assert "train_score" in overfit_results
    assert "val_score" in overfit_results
    
    # In this case, overfitting should be detected
    assert overfit_results["is_overfitting"] is True


def test_full_cv_pipeline(sample_cv_data, temp_data_dir):
    """Test the full cross-validation pipeline from data loading to result aggregation."""
    # 1. Run cross-validation
    cv_results = run_cross_validation(
        X=sample_cv_data["X"],
        y=sample_cv_data["y"],
        n_folds=5,
        random_state=42
    )
    
    # 2. Calculate metrics
    metrics = calculate_cv_metrics(cv_results)
    
    # 3. Save individual results
    cv_results_path = temp_data_dir / "cv_results.json"
    save_cv_results(cv_results, cv_results_path)
    
    metrics_path = temp_data_dir / "cv_metrics.json"
    save_cv_metrics_report(metrics, metrics_path)
    
    # 4. Simulate transferability results
    transfer_data = {
        "train_system": "Fe-Cr-Mo",
        "test_system": "Fe-Cr-V",
        "test_r2": 0.75,
        "test_mse": 0.12,
        "status": "acceptable"
    }
    transfer_path = temp_data_dir / "transferability_results.json"
    save_json_file(transfer_path, transfer_data)
    
    # 5. Simulate overfitting results
    overfit_data = {
        "is_overfitting": False,
        "train_score": 0.88,
        "val_score": 0.82,
        "score_difference": 0.06,
        "status": "no_overfitting"
    }
    overfit_path = temp_data_dir / "overfitting_report.json"
    save_json_file(overfit_path, overfit_data)
    
    # 6. Aggregate all results
    aggregated = aggregate_cross_validation_results(
        metrics_path,
        transfer_path,
        overfit_path
    )
    
    # 7. Verify aggregated results
    assert aggregated is not None
    assert aggregated["source"] == "cross_validation_aggregation"
    assert aggregated["summary"]["mean_r2"] == metrics["mean_r2"]
    assert aggregated["summary"]["std_r2"] == metrics["std_r2"]
    assert aggregated["summary"]["num_folds"] == 5
    assert aggregated["transferability"]["test_r2"] == 0.75
    assert aggregated["overfitting_analysis"]["is_overfitting"] is False
    assert len(aggregated["fold_details"]) == 5


def test_aggregation_with_missing_optional_files(sample_cv_data, temp_data_dir):
    """Test aggregation when optional files (transferability, overfitting) are missing."""
    # Run CV and save metrics
    cv_results = run_cross_validation(
        X=sample_cv_data["X"],
        y=sample_cv_data["y"],
        n_folds=5,
        random_state=42
    )
    metrics = calculate_cv_metrics(cv_results)
    
    metrics_path = temp_data_dir / "cv_metrics.json"
    save_cv_metrics_report(metrics, metrics_path)
    
    # Aggregate without optional files
    aggregated = aggregate_cross_validation_results(metrics_path)
    
    assert aggregated is not None
    assert aggregated["summary"]["mean_r2"] == metrics["mean_r2"]
    assert aggregated["transferability"] is None
    assert aggregated["overfitting_analysis"] is None
    assert "warnings" in aggregated


def test_integration_with_real_paths(temp_data_dir):
    """Integration test using actual PROCESSED_PATH structure."""
    # Create necessary directories
    processed_path = temp_data_dir / "processed"
    processed_path.mkdir(parents=True, exist_ok=True)
    
    # Mock PROCESSED_PATH
    with patch('code.config.PROCESSED_PATH', processed_path):
        # Generate sample data
        np.random.seed(123)
        X = np.random.rand(50, 3)
        y = 0.4 * X[:, 0] + 0.3 * X[:, 1] - 0.1 * X[:, 2] + np.random.normal(0, 0.05, 50)
        
        # Run full pipeline
        cv_results = run_cross_validation(X, y, n_folds=5, random_state=123)
        metrics = calculate_cv_metrics(cv_results)
        save_cv_results(cv_results, processed_path / "cv_results.json")
        save_cv_metrics_report(metrics, processed_path / "cv_metrics.json")
        
        # Load and verify
        loaded_metrics = load_json_file(processed_path / "cv_metrics.json")
        assert loaded_metrics["mean_r2"] == metrics["mean_r2"]
        assert loaded_metrics["std_r2"] == metrics["std_r2"]
        assert loaded_metrics["num_folds"] == 5


def test_edge_cases():
    """Test edge cases in cross-validation."""
    # Small dataset
    X_small = np.random.rand(10, 2)
    y_small = np.random.rand(10)
    
    cv_results_small = run_cross_validation(X_small, y_small, n_folds=3, random_state=42)
    assert len(cv_results_small["fold_scores"]) == 3
    
    # Single feature
    X_single = np.random.rand(20, 1)
    y_single = 0.5 * X_single[:, 0] + np.random.normal(0, 0.1, 20)
    
    cv_results_single = run_cross_validation(X_single, y_single, n_folds=4, random_state=42)
    assert len(cv_results_single["fold_scores"]) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
