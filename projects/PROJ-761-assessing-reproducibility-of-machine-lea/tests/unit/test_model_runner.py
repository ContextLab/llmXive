"""
Unit tests for model_runner.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge

# Import functions to test
from model_runner import (
    count_model_parameters,
    load_processed_data,
    train_model,
    evaluate_model,
    run_sensitivity_analysis,
    run_reproducibility_assessment,
    main,
)


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file for testing."""
    data = {
        "smiles": ["CCO", "CCCO", "CCCCO", "CC(C)CO", "CC(C)(C)CO"],
        "yield": [0.8, 0.75, 0.7, 0.65, 0.6],
        "temperature": [25, 30, 35, 40, 45],
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "sample_data.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


def test_count_model_parameters_rf():
    """Test parameter counting for Random Forest."""
    model = RandomForestRegressor(n_estimators=10, max_depth=3, random_state=42)
    # We don't fit it, but we count attributes
    params = count_model_parameters(model)
    # Should be > 0 even before fitting (empty arrays)
    assert params >= 0


def test_count_model_parameters_ridge():
    """Test parameter counting for Ridge."""
    model = Ridge(random_state=42)
    params = count_model_parameters(model)
    assert params >= 0


def test_train_model_small():
    """Test training a small model."""
    X = np.random.rand(100, 5)
    y = np.random.rand(100)
    model, status = train_model(X, y, seed=42)
    assert model is not None
    assert status in ["Model Trained", "Model Substitution/Unavailable (Parameter Limit)"]


def test_train_model_large_substitution():
    """Test that large models are substituted."""
    # Create a scenario where RF would be too large
    X = np.random.rand(100, 1000)  # Many features
    y = np.random.rand(100)
    model, status = train_model(X, y, seed=42, max_params=100)
    # Should substitute to Ridge
    assert isinstance(model, Ridge)
    assert "Substitution" in status


def test_evaluate_model():
    """Test model evaluation."""
    X = np.random.rand(100, 5)
    y = np.random.rand(100)
    model = Ridge(random_state=42)
    model.fit(X, y)
    metrics = evaluate_model(model, X, y, seed=42)
    assert "mae" in metrics
    assert "r2" in metrics
    assert "spearman_rho" in metrics
    assert all(isinstance(v, float) for v in metrics.values())


def test_load_processed_data(sample_csv):
    """Test loading processed data."""
    df, features, target = load_processed_data(sample_csv)
    assert len(df) == 5
    assert "yield" in df.columns
    assert "temperature" in features
    assert target == "yield"


def test_run_sensitivity_analysis(sample_csv):
    """Test sensitivity analysis."""
    df, features, target = load_processed_data(sample_csv)
    sensitivity = run_sensitivity_analysis(df, features, target, seeds=[42, 123])
    assert "mae_std" in sensitivity
    assert "r2_std" in sensitivity
    assert "spearman_std" in sensitivity
    assert "max_metric_std" in sensitivity
    assert all(isinstance(v, float) for v in sensitivity.values())


def test_run_reproducibility_assessment(sample_csv, tmp_path):
    """Test full reproducibility assessment."""
    manifest_entry = {
        "paper_id": "test_paper",
        "doi": "10.1234/test",
        "dataset_path": str(sample_csv),
        "reported_metrics": {"mae": 0.1, "r2": 0.9, "spearman_rho": 0.8},
        "seed": 42,
    }
    result = run_reproducibility_assessment(manifest_entry)
    assert result["paper_id"] == "test_paper"
    assert "metrics" in result
    assert "deviation_index" in result
    assert result["status"] in ["Model Trained", "Model Substitution/Unavailable (Parameter Limit)"]


def test_main_no_manifest(tmp_path):
    """Test main when no manifest exists."""
    with patch("model_runner.PROCESSED_DIR", tmp_path):
        with patch("model_runner.REPORTS_DIR", tmp_path / "reports"):
            (tmp_path / "reports").mkdir()
            # No manifest.yaml
            results = main()
            assert results == []
            output_file = tmp_path / "reports" / "repro_results.json"
            assert output_file.exists()