"""
Unit tests for save_model_metrics.py (T025).

This module tests the functionality of saving model metrics to a JSON file.
Since the main logic depends on data and model, we will mock the necessary parts.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

# Import the functions to test
from save_model_metrics import calculate_metrics, save_metrics, load_model, train_model

def test_calculate_metrics():
    """Test the calculate_metrics function."""
    # Create a mock model
    model = MagicMock()
    model.predict.return_value = np.array([1.0, 2.0, 3.0])

    X_test = np.array([[1], [2], [3]])
    y_test = np.array([1.0, 2.0, 3.0])

    metrics = calculate_metrics(model, X_test, y_test)

    assert 'r2' in metrics
    assert 'mse' in metrics
    assert metrics['r2'] == 1.0  # Perfect prediction
    assert metrics['mse'] == 0.0

def test_save_metrics():
    """Test the save_metrics function."""
    metrics = {'r2': 0.8, 'mse': 0.5}
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'model_metrics.json')
        save_metrics(metrics, output_path)

        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            saved_metrics = json.load(f)

        assert saved_metrics == metrics

def test_train_model():
    """Test the train_model function."""
    X_train = np.array([[1], [2], [3]])
    y_train = np.array([1.0, 2.0, 3.0])

    model = train_model(X_train, y_train)

    assert model is not None
    assert hasattr(model, 'predict')
    assert hasattr(model, 'fit')

    # Test prediction
    y_pred = model.predict(X_train)
    assert len(y_pred) == len(y_train)

def test_load_model_with_file():
    """Test loading a model from a file."""
    import pickle
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, 'model.pkl')
        model = train_model(np.array([[1]]), np.array([1.0]))
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)

        loaded_model = load_model(model_path)
        assert loaded_model is not None
        assert loaded_model.__class__.__name__ == 'RandomForestRegressor'

def test_load_model_without_file():
    """Test loading a model when file does not exist."""
    model = load_model('nonexistent_path.pkl')
    assert model is None

def test_main_function_integration():
    """Test the main function with mocked data and model."""
    with patch('save_model_metrics.load_interim_dataset') as mock_load_data, \
         patch('save_model_metrics.load_split_indices') as mock_load_split, \
         patch('save_model_metrics.train_model') as mock_train, \
         patch('save_model_metrics.save_metrics') as mock_save:

        # Mock data
        mock_df = pd.DataFrame({
            'resistance': [1.0, 2.0, 3.0, 4.0, 5.0],
            'metabolite_1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'metabolite_2': [0.5, 0.4, 0.3, 0.2, 0.1]
        })
        mock_load_data.return_value = mock_df

        mock_split_indices = {
            'train': [0, 1, 2],
            'test': [3, 4]
        }
        mock_load_split.return_value = mock_split_indices

        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([4.0, 5.0])
        mock_train.return_value = mock_model

        # Call main
        from save_model_metrics import main
        main()

        # Verify save_metrics was called
        assert mock_save.called
        # Get the metrics passed to save_metrics
        call_args = mock_save.call_args
        metrics = call_args[0][0]
        assert 'r2' in metrics
        assert 'mse' in metrics