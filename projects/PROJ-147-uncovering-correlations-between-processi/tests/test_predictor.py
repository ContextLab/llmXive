"""
Unit tests for the predictor module.

Tests FR-005 (predictions) and edge case handling for out-of-range inputs.
"""
import os
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib

from code.models.predictor import (
    load_model_and_scaler,
    check_input_ranges,
    predict_texture,
    run_prediction_pipeline
)
from code.utils.logging import get_logger

logger = get_logger(__name__)


@pytest.fixture
def temp_model_files():
    """Create temporary model and scaler files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create a simple trained model
        X_train = np.random.rand(100, 5)
        y_train = np.random.rand(100, 3)  # 3 texture outputs
        
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)
        
        scaler = StandardScaler()
        scaler.fit(X_train)
        
        model_path = tmpdir / "model.pkl"
        scaler_path = tmpdir / "scaler.pkl"
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        yield {
            'model_path': str(model_path),
            'scaler_path': str(scaler_path),
            'tmpdir': tmpdir
        }


@pytest.fixture
def training_stats():
    """Create training statistics for range checking."""
    return {
        'feature_0': {'min': 0.1, 'max': 0.9},
        'feature_1': {'min': 0.2, 'max': 0.8},
        'feature_2': {'min': 0.0, 'max': 1.0},
        'feature_3': {'min': 0.15, 'max': 0.85},
        'feature_4': {'min': 0.05, 'max': 0.95}
    }


def test_load_model_and_scaler(temp_model_files):
    """Test loading model and scaler from disk."""
    model, scaler = load_model_and_scaler(
        temp_model_files['model_path'],
        temp_model_files['scaler_path']
    )
    
    assert isinstance(model, RandomForestRegressor)
    assert isinstance(scaler, StandardScaler)
    assert model.n_estimators == 10


def test_load_model_and_scaler_not_found(temp_model_files):
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        load_model_and_scaler("nonexistent.pkl", temp_model_files['scaler_path'])
        
    with pytest.raises(FileNotFoundError):
        load_model_and_scaler(temp_model_files['model_path'], "nonexistent.pkl")


def test_check_input_ranges_all_within_range(training_stats):
    """Test range checking when all values are within training range."""
    input_data = pd.DataFrame({
        'feature_0': [0.3, 0.5, 0.7],
        'feature_1': [0.4, 0.5, 0.6],
        'feature_2': [0.2, 0.5, 0.8],
        'feature_3': [0.3, 0.5, 0.7],
        'feature_4': [0.3, 0.5, 0.7]
    })
    
    _, warnings = check_input_ranges(input_data, training_stats)
    
    assert len(warnings) == 0


def test_check_input_ranges_below_min(training_stats):
    """Test range checking when values are below minimum."""
    input_data = pd.DataFrame({
        'feature_0': [0.05, 0.5, 0.7],  # 0.05 < 0.1
        'feature_1': [0.4, 0.5, 0.6],
        'feature_2': [0.2, 0.5, 0.8],
        'feature_3': [0.3, 0.5, 0.7],
        'feature_4': [0.3, 0.5, 0.7]
    })
    
    _, warnings = check_input_ranges(input_data, training_stats)
    
    assert len(warnings) == 1
    assert "OUT_OF_RANGE_BELOW" in warnings[0] or "below min" in warnings[0].lower()


def test_check_input_ranges_above_max(training_stats):
    """Test range checking when values are above maximum."""
    input_data = pd.DataFrame({
        'feature_0': [0.3, 0.5, 0.95],  # 0.95 > 0.9
        'feature_1': [0.4, 0.5, 0.6],
        'feature_2': [0.2, 0.5, 0.8],
        'feature_3': [0.3, 0.5, 0.7],
        'feature_4': [0.3, 0.5, 0.7]
    })
    
    _, warnings = check_input_ranges(input_data, training_stats)
    
    assert len(warnings) == 1
    assert "OUT_OF_RANGE_ABOVE" in warnings[0] or "above max" in warnings[0].lower()


def test_check_input_ranges_mixed(training_stats):
    """Test range checking with both below min and above max."""
    input_data = pd.DataFrame({
        'feature_0': [0.05, 0.5, 0.95],  # Below and above
        'feature_1': [0.4, 0.5, 0.6],
        'feature_2': [0.2, 0.5, 0.8],
        'feature_3': [0.3, 0.5, 0.7],
        'feature_4': [0.3, 0.5, 0.7]
    })
    
    _, warnings = check_input_ranges(input_data, training_stats)
    
    assert len(warnings) == 2


def test_predict_texture(temp_model_files, training_stats):
    """Test the full prediction pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create input data
        input_data = pd.DataFrame({
            'feature_0': [0.3, 0.5, 0.7],
            'feature_1': [0.4, 0.5, 0.6],
            'feature_2': [0.2, 0.5, 0.8],
            'feature_3': [0.3, 0.5, 0.7],
            'feature_4': [0.3, 0.5, 0.7]
        })
        
        input_path = tmpdir / "input.csv"
        input_data.to_csv(input_path, index=False)
        
        stats_path = tmpdir / "stats.json"
        with open(stats_path, 'w') as f:
            json.dump(training_stats, f)
        
        output_path = str(tmpdir / "predictions.csv")
        new_path = str(tmpdir / "new_predictions.csv")
        
        # Run prediction
        result = predict_texture(
            model=joblib.load(temp_model_files['model_path']),
            scaler=joblib.load(temp_model_files['scaler_path']),
            input_data=input_data,
            training_stats=training_stats,
            output_path=output_path,
            new_sample_path=new_path
        )
        
        # Verify results
        assert isinstance(result, pd.DataFrame)
        assert 'sample_id' in result.columns
        assert 'texture_100' in result.columns or 'texture_output_0' in result.columns
        assert len(result) == 3
        
        # Verify files were created
        assert Path(output_path).exists()
        assert Path(new_path).exists()


def test_run_prediction_pipeline(temp_model_files, training_stats):
    """Test the complete pipeline function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create input data
        input_data = pd.DataFrame({
            'feature_0': [0.3, 0.5, 0.7],
            'feature_1': [0.4, 0.5, 0.6],
            'feature_2': [0.2, 0.5, 0.8],
            'feature_3': [0.3, 0.5, 0.7],
            'feature_4': [0.3, 0.5, 0.7]
        })
        
        input_path = tmpdir / "input.csv"
        input_data.to_csv(input_path, index=False)
        
        stats_path = tmpdir / "stats.json"
        with open(stats_path, 'w') as f:
            json.dump(training_stats, f)
        
        output_path = str(tmpdir / "predictions.csv")
        new_path = str(tmpdir / "new_predictions.csv")
        
        # Run pipeline
        result = run_prediction_pipeline(
            model_path=temp_model_files['model_path'],
            scaler_path=temp_model_files['scaler_path'],
            input_data_path=str(input_path),
            training_stats_path=str(stats_path),
            output_predictions_path=output_path,
            new_predictions_path=new_path
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert Path(output_path).exists()