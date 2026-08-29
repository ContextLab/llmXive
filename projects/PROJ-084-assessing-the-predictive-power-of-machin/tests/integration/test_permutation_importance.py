"""
Integration test for permutation importance computation (T032).
Verifies that the evaluation module can compute importance scores on a small dataset.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from modeling.evaluate import compute_permutation_importance, evaluate_model
from utils.io import save_parquet


@pytest.fixture
def mock_test_data(tmp_path):
    """Create a small mock dataset for testing."""
    n_samples = 200
    n_features = 20  # Small number for speed
    n_classes = 3

    # Generate synthetic fingerprints (0/1)
    X = np.random.randint(0, 2, size=(n_samples, n_features)).astype(float)
    # Generate synthetic yields (0-100)
    y = np.random.uniform(0, 100, size=n_samples)
    # Generate reaction classes
    classes = np.random.choice(['Class_A', 'Class_B', 'Class_C'], size=n_samples)

    df = pd.DataFrame({
        'fingerprint_ecfp': list(X),
        'yield': y,
        'reaction_class': classes
    })

    test_data_path = tmp_path / "test_set.parquet"
    save_parquet(df, test_data_path)

    return test_data_path, X, y, classes


@pytest.fixture
def mock_model(tmp_path, mock_test_data):
    """Train a small Random Forest model for testing."""
    _, X, y, _ = mock_test_data
    model = RandomForestRegressor(n_estimators=10, max_depth=3, random_state=42)
    model.fit(X, y)

    model_path = tmp_path / "best_models"
    model_path.mkdir(parents=True, exist_ok=True)
    import joblib
    joblib.dump(model, model_path / "random_forest_model.pkl")

    return model_path


def test_compute_permutation_importance(mock_test_data, mock_model):
    """Test the compute_permutation_importance function directly."""
    _, X, y, _ = mock_test_data
    import joblib
    model = joblib.load(mock_model / "random_forest_model.pkl")

    feature_names = [f"ECFP_{i}" for i in range(X.shape[1])]

    result = compute_permutation_importance(
        model, X, y, feature_names=feature_names, n_repeats=2
    )

    # Assertions
    assert result["model_type"] == "RandomForest"
    assert result["n_features"] == X.shape[1]
    assert result["n_repeats"] == 2
    assert "importance_scores" in result
    assert "summary" in result

    # Check that importance scores are present
    scores = result["importance_scores"]
    assert len(scores) == X.shape[1]
    assert all(isinstance(s["importance"], float) for s in scores)

    # Check summary stats
    assert "mean_importance" in result["summary"]
    assert "std_importance" in result["summary"]


def test_evaluate_model_integration(mock_test_data, mock_model, tmp_path):
    """Test the full evaluate_model function end-to-end."""
    test_data_path, _, _, _ = mock_test_data
    output_path = tmp_path / "evaluation_results.json"

    results = evaluate_model(test_data_path, mock_model, output_path)

    # Verify file was created
    assert output_path.exists()

    # Verify content structure
    assert "overall_metrics" in results
    assert "per_class_metrics" in results
    assert "permutation_importance" in results
    assert "test_set_size" in results

    # Check metrics keys
    metrics = results["overall_metrics"]
    assert "R2" in metrics
    assert "RMSE" in metrics
    assert "MAE" in metrics

    # Check per-class metrics
    per_class = results["per_class_metrics"]
    assert "model_type" in per_class
    assert "per_class_metrics" in per_class
    assert len(per_class["per_class_metrics"]) > 0

    # Check importance
    importance = results["permutation_importance"]
    assert "importance_scores" in importance
    assert len(importance["importance_scores"]) > 0

    # Verify JSON file content
    with open(output_path, 'r') as f:
        saved_results = json.load(f)
    assert saved_results == results