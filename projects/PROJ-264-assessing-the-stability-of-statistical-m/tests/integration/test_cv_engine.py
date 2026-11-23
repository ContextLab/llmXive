"""
Integration tests for the repeated cross-validation engine.
"""
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.datasets import fetch_openml

from code.config import RESULTS_DIR
from code.data_loader import load_datasets
from code.evaluator import run_repeated_stratified_cv
from code.preprocessor import preprocess_data
from code.results_writer import write_raw_evaluations


@pytest.fixture
def test_fixture_iris_binary():
    """
    Creates a binary subset of Iris from OpenML for testing.
    Returns:
        dict: Dictionary containing X, y, dataset_id, and dataset_name.
    """
    # Fetch Iris dataset from OpenML
    # OpenML ID for Iris is 61
    iris = fetch_openml(name="iris", version=1, as_frame=True)
    
    # Convert to binary classification: Setosa vs Non-Setosa
    # Iris target has 3 classes: 'setosa', 'versicolor', 'virginica'
    y_binary = (iris.target != "setosa").astype(int)
    X_binary = iris.data
    
    dataset_id = 61
    dataset_name = "iris_binary"
    
    return {
        "X": X_binary,
        "y": y_binary,
        "dataset_id": dataset_id,
        "dataset_name": dataset_name,
        "n_samples": len(y_binary),
        "n_features": X_binary.shape[1]
    }


def test_repeated_cv_iris_row_count(test_fixture_iris_binary):
    """
    Test that the expected number of rows are generated.
    With 10 repeats and 3 models (LR, RF, SVM), and 10 folds:
    Total rows = 10 repeats * 10 folds * 3 models = 300 rows.
    """
    data = test_fixture_iris_binary
    X = data["X"]
    y = data["y"]
    dataset_id = data["dataset_id"]
    dataset_name = data["dataset_name"]
    
    # Preprocess data
    X_processed, _ = preprocess_data(X, y, is_training=True)
    
    # Run repeated stratified CV
    results = run_repeated_stratified_cv(
        X_processed,
        y,
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        n_splits=10,
        n_repeats=10,
        models=None  # Use default models
    )
    
    # Expected: 10 repeats * 10 folds * 3 models = 300 rows
    expected_rows = 10 * 10 * 3
    assert len(results) == expected_rows, (
        f"Expected {expected_rows} rows, got {len(results)}. "
        f"Results shape: {results.shape}"
    )
    
    # Verify columns exist
    expected_columns = ['dataset_id', 'model_name', 'fold_id', 'repeat_id', 'accuracy', 'f1_score']
    assert list(results.columns) == expected_columns, (
        f"Expected columns {expected_columns}, got {list(results.columns)}"
    )


def test_repeated_cv_iris_variance(test_fixture_iris_binary):
    """
    Test that there is non-zero variance in accuracy scores across multiple repeats
    for at least one model.
    
    This test verifies that the repeated cross-validation produces varied results
    due to different train/test splits, which is expected behavior.
    """
    data = test_fixture_iris_binary
    X = data["X"]
    y = data["y"]
    dataset_id = data["dataset_id"]
    dataset_name = data["dataset_name"]
    
    # Preprocess data
    X_processed, _ = preprocess_data(X, y, is_training=True)
    
    # Run repeated stratified CV
    results = run_repeated_stratified_cv(
        X_processed,
        y,
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        n_splits=10,
        n_repeats=10,
        models=None  # Use default models
    )
    
    # Check that at least one model has non-zero variance in accuracy
    models = results['model_name'].unique()
    variance_found = False
    
    for model in models:
        model_results = results[results['model_name'] == model]
        accuracy_std = model_results['accuracy'].std()
        
        if accuracy_std > 0:
            variance_found = True
            break
    
    assert variance_found, (
        "No model showed non-zero variance in accuracy scores. "
        "This suggests the CV splits may be identical or there's an issue with the evaluation."
    )
    
    # Additional check: verify that variance is within expected bounds
    # (not too high, not zero)
    for model in models:
        model_results = results[results['model_name'] == model]
        accuracy_std = model_results['accuracy'].std()
        accuracy_mean = model_results['accuracy'].mean()
        
        # CV should be reasonable (not 0, not extremely high)
        cv = accuracy_std / accuracy_mean if accuracy_mean > 0 else 0
        assert 0 < cv < 1.0, (
            f"Model {model} has unexpected CV: {cv}. "
            f"Mean: {accuracy_mean}, Std: {accuracy_std}"
        )
    
    # Verify that different repeats produce different results
    repeat_ids = results['repeat_id'].unique()
    assert len(repeat_ids) == 10, f"Expected 10 repeats, got {len(repeat_ids)}"
    
    # Check that accuracy varies across repeats for at least one model
    sample_model = results['model_name'].iloc[0]
    model_data = results[results['model_name'] == sample_model]
    
    # Group by repeat and calculate mean accuracy per repeat
    repeat_means = model_data.groupby('repeat_id')['accuracy'].mean()
    
    # There should be variation in repeat means
    repeat_std = repeat_means.std()
    assert repeat_std > 0, (
        f"All repeats produced identical mean accuracy for {sample_model}. "
        f"Repeat means: {repeat_means.values}"
    )