"""
Unit tests for SHAP interpretation utilities.
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import GradientBoostingRegressor

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.models.interpret import (
    extract_feature_importance,
    save_results,
    generate_shap_plot
)
import shap

@pytest.fixture
def mock_shap_values():
    """Create mock SHAP values for testing."""
    # Simulate 10 samples, 3 features
    np.random.seed(42)
    values = np.random.randn(10, 3)
    return shap.Explanation(values=values, data=np.random.randn(10, 3), feature_names=["f1", "f2", "f3"])

@pytest.fixture
def mock_data():
    """Create mock feature DataFrame."""
    np.random.seed(42)
    data = {
        "f1": np.random.randn(10),
        "f2": np.random.randn(10),
        "f3": np.random.randn(10)
    }
    return pd.DataFrame(data)

def test_extract_feature_importance(mock_shap_values, mock_data):
    """Test that feature importance extraction returns correct structure and sorting."""
    result = extract_feature_importance(mock_shap_values, mock_data)

    # Check structure
    assert isinstance(result, list)
    assert len(result) == 3

    # Check keys
    for item in result:
        assert "feature" in item
        assert "mean_abs_shap" in item
        assert "correlation" in item
        assert "direction" in item
        assert item["direction"] in ["positive", "negative"]

    # Check sorting (descending by mean_abs_shap)
    shap_values = [item["mean_abs_shap"] for item in result]
    assert shap_values == sorted(shap_values, reverse=True)

def test_save_results(tmp_path):
    """Test that save_results writes valid JSON."""
    test_data = [
        {"feature": "f1", "mean_abs_shap": 0.5, "correlation": 0.8, "direction": "positive"},
        {"feature": "f2", "mean_abs_shap": 0.3, "correlation": -0.2, "direction": "negative"}
    ]
    output_file = tmp_path / "test_results.json"

    save_results(test_data, output_file)

    assert output_file.exists()
    with open(output_file, 'r') as f:
        loaded_data = json.load(f)

    assert loaded_data == test_data

def test_generate_shap_plot(tmp_path, mock_shap_values, mock_data):
    """Test that generate_shap_plot creates a file."""
    output_file = tmp_path / "test_plot.png"

    # Mock shap.summary_plot to avoid actual plotting overhead in unit test
    # but verify the call happens
    with patch('src.models.interpret.shap.summary_plot') as mock_summary:
        with patch('src.models.interpret.plt.savefig') as mock_save:
            with patch('src.models.interpret.plt.close'):
                with patch('src.models.interpret.plt.figure'):
                    generate_shap_plot(mock_shap_values, mock_data, output_file)

                    # Verify shap.summary_plot was called
                    assert mock_summary.called
                    # Verify savefig was called with the correct path
                    assert mock_save.called
                    # Verify the file path passed to savefig
                    call_args = mock_save.call_args
                    assert call_args[0][0] == output_file