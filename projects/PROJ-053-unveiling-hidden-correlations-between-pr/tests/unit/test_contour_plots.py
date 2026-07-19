"""
Unit tests for contour plot generation logic.
"""
import os
import sys
import json
import tempfile
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from viz.contour_plots import (
    generate_contour_grid,
    predict_with_uncertainty,
    create_contour_plot,
    create_uncertainty_heatmap
)

@pytest.fixture
def mock_feature_names():
    return ["laser_power", "scan_speed", "layer_thickness", "alloy_type_A", "alloy_type_B"]

@pytest.fixture
def mock_X_test():
    # Dummy test data
    return np.random.rand(10, 5)

@pytest.fixture
def mock_normalization_bounds():
    return {
        "laser_power": {"min": 100, "max": 400},
        "scan_speed": {"min": 500, "max": 1500},
        "layer_thickness": {"min": 0.03, "max": 0.05},
        "alloy_type_A": {"min": 0, "max": 1},
        "alloy_type_B": {"min": 0, "max": 1}
    }

def test_generate_contour_grid(mock_feature_names, mock_normalization_bounds):
    """Test grid generation logic."""
    with patch('viz.contour_plots.load_normalization_bounds', return_value=mock_normalization_bounds):
        with patch('viz.contour_plots.get_processed_data_dir', return_value='/tmp'):
            with patch('viz.contour_plots.pd.read_csv') as mock_read_csv:
                # Mock dataframe with means
                mock_df = MagicMock()
                mock_df.__getitem__ = lambda self, key: np.random.rand(100)
                mock_df.mean.return_value = np.random.rand(5)
                mock_read_csv.return_value = mock_df

                X1, X2, X_grid, p_min, p_max, s_min, s_max = generate_contour_grid(
                    np.zeros((10, 5)), mock_feature_names, resolution=10
                )

                assert X1.shape == (10, 10)
                assert X2.shape == (10, 10)
                assert X_grid.shape == (100, 5)
                assert p_min == 100
                assert p_max == 400
                assert s_min == 500
                assert s_max == 1500

def test_predict_with_uncertainty():
    """Test prediction with uncertainty."""
    mock_model = MagicMock()
    mock_model.predict.return_value = (np.array([1.0, 2.0]), np.array([0.1, 0.2]))
    
    X = np.array([[0.5, 0.5, 0.5, 0.5, 0.5]])
    mean, std = predict_with_uncertainty(mock_model, X)
    
    assert mean.shape == (2,)
    assert std.shape == (2,)
    assert np.allclose(mean, [1.0, 2.0])
    assert np.allclose(std, [0.1, 0.2])

def test_create_contour_plot(tmp_path):
    """Test contour plot creation."""
    X1, X2 = np.meshgrid(np.linspace(0, 1, 10), np.linspace(0, 1, 10))
    Y_mean = np.random.rand(10, 10)
    Y_std = np.random.rand(10, 10)
    
    output_path = os.path.join(tmp_path, "test_contour.png")
    
    create_contour_plot(
        X1, X2, Y_mean, Y_std,
        0, 1, 0, 1,
        "Yield Strength",
        output_path
    )
    
    assert os.path.exists(output_path)

def test_create_uncertainty_heatmap(tmp_path):
    """Test uncertainty heatmap creation."""
    X1, X2 = np.meshgrid(np.linspace(0, 1, 10), np.linspace(0, 1, 10))
    Y_std = np.random.rand(10, 10)
    
    output_path = os.path.join(tmp_path, "test_heatmap.png")
    
    create_uncertainty_heatmap(X1, X2, Y_std, output_path)
    
    assert os.path.exists(output_path)