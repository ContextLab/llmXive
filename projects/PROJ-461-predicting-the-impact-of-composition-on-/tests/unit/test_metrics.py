"""
Unit tests for code/analysis/metrics.py (T026).
"""
import json
import os
import pickle
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

# Mock imports to avoid dependency issues in unit tests
from config import Config


@pytest.fixture
def temp_config():
    """Create a temporary config for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config = Config(
            seed=42,
            data_dir=tmp_path / "data",
            model_dir=tmp_path / "models",
            report_dir=tmp_path / "reports"
        )
        config.data_dir.mkdir(parents=True, exist_ok=True)
        config.model_dir.mkdir(parents=True, exist_ok=True)
        config.report_dir.mkdir(parents=True, exist_ok=True)
        yield config


@pytest.fixture
def sample_data(temp_config):
    """Create sample data for testing."""
    # Create a simple DataFrame with required columns
    data = {
        "density": [2.5, 3.0, 2.8, 3.2, 2.9],
        "rho_baseline": [2.4, 2.9, 2.7, 3.1, 2.85],
        "density_residual": [0.1, 0.1, 0.1, 0.1, 0.05],
        "mean_atomic_mass": [10.0, 20.0, 15.0, 25.0, 18.0],
        "feature_1": [1.0, 2.0, 1.5, 2.5, 1.8],
        "composition": ["Zr50Cu50", "Zr60Cu40", "Zr55Cu45", "Zr65Cu35", "Zr52Cu48"],
    }
    df = pd.DataFrame(data)
    csv_path = temp_config.data_dir / "clean_data.csv"
    df.to_csv(csv_path, index=False)
    return df


@pytest.fixture
def mock_model(temp_config, sample_data):
    """Create a mock trained model."""
    # Train a simple model on the sample data to make it realistic
    feature_cols = ["feature_1"]
    X = sample_data[feature_cols].values
    y = sample_data["density_residual"].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    model_path = temp_config.model_dir / "model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    return model


def test_load_model(temp_config, mock_model):
    """Test loading the model."""
    from code.analysis.metrics import load_model
    
    model = load_model(temp_config)
    assert model is not None
    assert hasattr(model, 'predict')


def test_load_processed_data(temp_config, sample_data):
    """Test loading processed data."""
    from code.analysis.metrics import load_processed_data
    
    df = load_processed_data(temp_config)
    assert len(df) == len(sample_data)
    assert "density" in df.columns
    assert "rho_baseline" in df.columns


def test_calculate_baseline_metrics(temp_config, sample_data):
    """Test baseline metric calculation."""
    from code.analysis.metrics import calculate_baseline_metrics
    import logging
    
    logger = logging.getLogger("test")
    
    lmr_mae, mass_only_mae = calculate_baseline_metrics(sample_data, logger)
    
    # LMR MAE: |actual - baseline|
    expected_lmr_mae = mean_absolute_error(
        sample_data["density"].values, 
        sample_data["rho_baseline"].values
    )
    assert np.isclose(lmr_mae, expected_lmr_mae)
    
    # Mass-Only MAE: fit linear model on mean_atomic_mass vs residual
    X = sample_data["mean_atomic_mass"].values.reshape(-1, 1)
    y = sample_data["density_residual"].values
    mass_model = LinearRegression()
    mass_model.fit(X, y)
    predictions = mass_model.predict(X)
    expected_mass_mae = mean_absolute_error(y, predictions)
    
    assert np.isclose(mass_only_mae, expected_mass_mae)


def test_calculate_model_metrics(temp_config, sample_data, mock_model):
    """Test main model metric calculation."""
    from code.analysis.metrics import calculate_model_metrics
    import logging
    
    logger = logging.getLogger("test")
    
    model_mae, model_r2 = calculate_model_metrics(mock_model, sample_data, logger)
    
    # Verify against sklearn metrics
    feature_cols = ["feature_1"]
    X = sample_data[feature_cols].values
    y = sample_data["density_residual"].values
    
    predictions = mock_model.predict(X)
    expected_mae = mean_absolute_error(y, predictions)
    expected_r2 = r2_score(y, predictions)
    
    assert np.isclose(model_mae, expected_mae)
    assert np.isclose(model_r2, expected_r2)


def test_save_metrics(temp_config, sample_data, mock_model):
    """Test saving metrics to JSON."""
    from code.analysis.metrics import main
    import logging
    
    logger = logging.getLogger("test")
    
    # Run the main logic
    with patch('code.analysis.metrics.load_model', return_value=mock_model), \
         patch('code.analysis.metrics.load_processed_data', return_value=sample_data), \
         patch('code.analysis.metrics.get_logger', return_value=logger):
        
        main()
    
    # Verify file exists
    metrics_path = temp_config.report_dir / "metrics.json"
    assert metrics_path.exists()
    
    with open(metrics_path) as f:
        metrics = json.load(f)
    
    assert "model_mae" in metrics
    assert "model_r2" in metrics
    assert "lmr_baseline_mae" in metrics
    assert "mass_only_baseline_mae" in metrics
    assert metrics["status"] == "success"