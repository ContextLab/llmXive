"""
Unit tests for code/models/save_artifacts.py (T024).
Tests saving models to pickle and coefficients to JSON.
"""
import os
import json
import pickle
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Mock the config module to use a temporary directory for tests
@pytest.fixture
def temp_models_dir(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    with patch('models.save_artifacts.MODELS_DIR', str(models_dir)):
        yield models_dir

def test_save_model_to_pickle(temp_models_dir):
    """Test that a mock model is saved to a pickle file."""
    from models.save_artifacts import save_model_to_pickle

    mock_model = MagicMock()
    filename = "test_model.pkl"

    save_model_to_pickle(mock_model, filename)

    filepath = temp_models_dir / filename
    assert filepath.exists()

    # Verify the content can be loaded
    with open(filepath, 'rb') as f:
        loaded_model = pickle.load(f)
    assert loaded_model is mock_model

def test_save_linear_coefficients(temp_models_dir):
    """Test that coefficients are saved to a JSON file."""
    from models.save_artifacts import save_linear_coefficients

    coeffs = {
        "size_mismatch": 0.54,
        "intercept": 1.23,
        "p_value": 0.002,
        "r_squared": 0.78
    }
    filename = "test_coef.json"

    save_linear_coefficients(coeffs, filename)

    filepath = temp_models_dir / filename
    assert filepath.exists()

    with open(filepath, 'r') as f:
        loaded_coeffs = json.load(f)
    assert loaded_coeffs == coeffs

def test_save_model_to_pickle_missing_dir():
    """Test that FileNotFoundError is raised if models dir doesn't exist."""
    from models.save_artifacts import save_model_to_pickle

    mock_model = MagicMock()
    filename = "test_model.pkl"

    with patch('models.save_artifacts.MODELS_DIR', '/nonexistent/path/models'):
        with pytest.raises(FileNotFoundError):
            save_model_to_pickle(mock_model, filename)

def test_save_linear_coefficients_missing_dir():
    """Test that FileNotFoundError is raised if models dir doesn't exist."""
    from models.save_artifacts import save_linear_coefficients

    coeffs = {"size_mismatch": 0.5}
    filename = "test_coef.json"

    with patch('models.save_artifacts.MODELS_DIR', '/nonexistent/path/models'):
        with pytest.raises(FileNotFoundError):
            save_linear_coefficients(coeffs, filename)