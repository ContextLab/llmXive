"""
Unit tests for cross-validation functionality.
"""
import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold

from code.cross_validation import run_cross_validation, record_metrics_to_file, compare_cv_results
from code.config import SEED


@pytest.fixture
def sample_data():
    """Create sample feature and target data for testing."""
    np.random.seed(SEED)
    n_samples = 100
    n_features = 5

    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f"feature_{i}" for i in range(n_features)]
    )
    y = pd.Series(np.random.randn(n_samples) * 10 + 5, name="target")

    return X, y


@pytest.fixture
def sample_model():
    """Create a simple Random Forest model for testing."""
    return RandomForestRegressor(n_estimators=10, random_state=SEED)


def test_run_cross_validation_returns_correct_structure(sample_data, sample_model):
    """Test that run_cross_validation returns a dictionary with expected keys."""
    X, y = sample_data
    result = run_cross_validation(X, y, sample_model, n_splits=5, seed=SEED)

    expected_keys = [
        "cv_r2_scores", "cv_mae_scores", "mean_r2", "mean_mae",
        "std_r2", "std_mae", "n_splits", "seed"
    ]

    for key in expected_keys:
        assert key in result, f"Missing key: {key}"

    assert len(result["cv_r2_scores"]) == 5
    assert len(result["cv_mae_scores"]) == 5
    assert isinstance(result["mean_r2"], float)
    assert isinstance(result["mean_mae"], float)


def test_cross_validation_scores_are_realistic(sample_data, sample_model):
    """Test that CV scores are within realistic ranges."""
    X, y = sample_data
    result = run_cross_validation(X, y, sample_model, n_splits=5, seed=SEED)

    # R² should be between -inf and 1 (typically > -1 for reasonable models)
    assert all(-2 <= r2 <= 1 for r2 in result["cv_r2_scores"]), "R² scores out of expected range"

    # MAE should be positive
    assert all(mae >= 0 for mae in result["cv_mae_scores"]), "MAE scores should be non-negative"

    # Mean values should be within the range of individual scores
    assert result["mean_r2"] >= min(result["cv_r2_scores"])
    assert result["mean_r2"] <= max(result["cv_r2_scores"])


def test_reproducibility_with_same_seed(sample_data, sample_model):
    """Test that running CV with the same seed produces identical results."""
    X, y = sample_data

    result1 = run_cross_validation(X, y, sample_model, n_splits=5, seed=SEED)
    result2 = run_cross_validation(X, y, sample_model, n_splits=5, seed=SEED)

    assert result1["mean_r2"] == result2["mean_r2"], "Results should be identical with same seed"
    assert result1["mean_mae"] == result2["mean_mae"], "Results should be identical with same seed"


def test_record_metrics_to_file_creates_json(sample_data, sample_model, tmp_path):
    """Test that record_metrics_to_file creates a valid JSON file."""
    X, y = sample_data
    result = run_cross_validation(X, y, sample_model, n_splits=5, seed=SEED)

    output_path = tmp_path / "test_cv_results.json"
    record_metrics_to_file(result, str(output_path), "test_model")

    assert output_path.exists(), "Output file should be created"

    import json
    with open(output_path, 'r') as f:
        saved_data = json.load(f)

    assert "cv_r2_scores" in saved_data
    assert "model_name" in saved_data
    assert saved_data["model_name"] == "test_model"


def test_compare_cv_results_returns_dataframe(tmp_path):
    """Test that compare_cv_results returns a DataFrame with correct structure."""
    results = {
        "model_a": {"mean_r2": 0.8, "std_r2": 0.1, "mean_mae": 0.5, "std_mae": 0.05, "n_splits": 5},
        "model_b": {"mean_r2": 0.7, "std_r2": 0.15, "mean_mae": 0.6, "std_mae": 0.08, "n_splits": 5}
    }

    df = compare_cv_results(results)

    assert isinstance(df, pd.DataFrame)
    assert "model" in df.columns
    assert "mean_r2" in df.columns
    assert len(df) == 2

    # Should be sorted by mean_r2 descending
    assert df.iloc[0]["mean_r2"] >= df.iloc[1]["mean_r2"]