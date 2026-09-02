"""
Unit tests for baseline models (T022).
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json

from src.models.baseline import (
    load_preprocessed_data,
    train_baseline_models,
    BASELINE_FEATURES,
    TARGET_COLUMN
)


@pytest.fixture
def sample_graph_data(tmp_path):
    """Create a sample graphs.json file for testing."""
    data = [
        {
            "molecule": {
                "pKa": 10.5,
                "MW": 120.0,
                "Taft_Es": -0.5,
                "Taft_Es_s": -0.2,
                "Charton_nu": 0.8,
                "Hammett_sigma_p": 0.0,
                "Molar_Refractivity": 35.0
            },
            "reaction": {
                "normalized_log_rate": 2.5,
                "scaffold": "scaffold_A"
            }
        },
        {
            "molecule": {
                "pKa": 9.2,
                "MW": 135.0,
                "Taft_Es": -0.8,
                "Taft_Es_s": -0.4,
                "Charton_nu": 1.1,
                "Hammett_sigma_p": 0.2,
                "Molar_Refractivity": 40.0
            },
            "reaction": {
                "normalized_log_rate": 1.8,
                "scaffold": "scaffold_B"
            }
        },
        {
            "molecule": {
                "pKa": 11.0,
                "MW": 110.0,
                "Taft_Es": -0.3,
                "Taft_Es_s": -0.1,
                "Charton_nu": 0.6,
                "Hammett_sigma_p": -0.1,
                "Molar_Refractivity": 30.0
            },
            "reaction": {
                "normalized_log_rate": 3.2,
                "scaffold": "scaffold_A"
            }
        }
    ]
    
    file_path = tmp_path / "graphs.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    return str(file_path)


def test_load_preprocessed_data(sample_graph_data):
    """Test that load_preprocessed_data correctly parses JSON and handles missing values."""
    df = load_preprocessed_data(sample_graph_data)
    
    assert len(df) == 3
    assert set(BASELINE_FEATURES).issubset(df.columns)
    assert TARGET_COLUMN in df.columns
    assert 'scaffold' in df.columns
    
    # Check that no NaNs exist in features after imputation
    for col in BASELINE_FEATURES:
        assert not df[col].isna().any(), f"Column {col} should not have NaNs after imputation"


def test_train_baseline_models(sample_graph_data, tmp_path):
    """Test that training produces models and metrics."""
    df = load_preprocessed_data(sample_graph_data)
    output_dir = tmp_path / "models"
    
    models, metrics = train_baseline_models(df, str(output_dir))
    
    assert 'linear_regression' in models
    assert 'random_forest' in models
    assert 'linear_regression' in metrics
    assert 'random_forest' in metrics
    
    # Check metrics structure
    for model_name, model_metrics in metrics.items():
        assert 'mae' in model_metrics
        assert 'r2' in model_metrics
        assert isinstance(model_metrics['mae'], float)
        assert isinstance(model_metrics['r2'], float)
    
    # Check files were saved
    assert (output_dir / "baseline_linear_regression.joblib").exists()
    assert (output_dir / "baseline_random_forest.joblib").exists()
    assert (output_dir / "training_metrics.json").exists()


def test_train_with_missing_values(sample_graph_data, tmp_path):
    """Test training handles missing values via imputation."""
    # Modify data to have a missing value
    data_path = Path(sample_graph_data)
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    data[0]['molecule']['pKa'] = None # Introduce a missing value
    
    with open(data_path, 'w') as f:
        json.dump(data, f)
    
    df = load_preprocessed_data(str(data_path))
    output_dir = tmp_path / "models_missing"
    
    # Should not raise an error
    models, metrics = train_baseline_models(df, str(output_dir))
    
    assert 'random_forest' in models
    assert metrics['random_forest']['mae'] >= 0


def test_empty_data_raises_error(tmp_path):
    """Test that empty data raises ValueError."""
    file_path = tmp_path / "empty.json"
    with open(file_path, 'w') as f:
        json.dump([], f)
    
    with pytest.raises(ValueError, match="No valid records found"):
        load_preprocessed_data(str(file_path))
