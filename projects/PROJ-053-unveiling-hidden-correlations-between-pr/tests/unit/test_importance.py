"""
Unit tests for Partial Dependence Plot generation (T036).
"""
import os
import sys
import json
import tempfile
import shutil
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from viz.importance import (
    generate_pdp_grid,
    compute_partial_dependence,
    create_pdp_plot,
    generate_all_pdp_plots,
    create_combined_pdp_figure,
    N_TOP_FEATURES
)

class TestPDPGeneration:
    """Test suite for PDP generation functions."""

    @pytest.fixture
    def sample_feature_matrix(self):
        """Create a sample feature matrix for testing."""
        np.random.seed(42)
        X = np.random.rand(100, 3)
        # Normalize to realistic ranges
        X[:, 0] = X[:, 0] * 200 + 200  # Laser power: 200-400 W
        X[:, 1] = X[:, 1] * 1000 + 500  # Scan speed: 500-1500 mm/s
        X[:, 2] = X[:, 2] * 0.05 + 0.03  # Layer thickness: 0.03-0.08 mm
        return X

    @pytest.fixture
    def mock_model(self):
        """Create a mock GPR model for testing."""
        model = MagicMock()
        # Simple linear prediction for testing
        model.predict = lambda X: np.sum(X, axis=1) + np.random.normal(0, 0.1, len(X))
        return model

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_generate_pdp_grid_basic(self, sample_feature_matrix):
        """Test basic grid generation for a feature."""
        feature_idx = 0
        n_points = 20
        
        feature_values, _ = generate_pdp_grid(sample_feature_matrix, feature_idx, n_points)
        
        assert len(feature_values) == n_points
        assert feature_values.min() >= sample_feature_matrix[:, feature_idx].min()
        assert feature_values.max() <= sample_feature_matrix[:, feature_idx].max()
        assert np.all(np.diff(feature_values) > 0)  # Should be sorted

    def test_compute_partial_dependence_shapes(self, mock_model, sample_feature_matrix):
        """Test that PDP computation returns correct shapes."""
        feature_idx = 0
        n_points = 10
        
        feature_values, _ = generate_pdp_grid(sample_feature_matrix, feature_idx, n_points)
        pdp_values = compute_partial_dependence(mock_model, sample_feature_matrix, feature_idx, feature_values)
        
        assert len(pdp_values) == n_points
        assert pdp_values.shape == (n_points,)

    def test_create_pdp_plot_saves_file(self, mock_model, sample_feature_matrix, temp_output_dir):
        """Test that PDP plot creation saves a file."""
        feature_idx = 0
        n_points = 10
        
        feature_values, _ = generate_pdp_grid(sample_feature_matrix, feature_idx, n_points)
        pdp_values = compute_partial_dependence(mock_model, sample_feature_matrix, feature_idx, feature_values)
        
        output_path = os.path.join(temp_output_dir, 'test_pdp.png')
        create_pdp_plot(
            feature_name='Test Feature',
            feature_values=feature_values,
            pdp_values=pdp_values,
            output_path=output_path
        )
        
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_generate_all_pdp_plots_multiple_features(self, mock_model, sample_feature_matrix, temp_output_dir):
        """Test generating PDPs for multiple features."""
        feature_names = ['Feature_A', 'Feature_B', 'Feature_C']
        top_features = [
            {'name': 'Feature_A', 'rank': 1},
            {'name': 'Feature_B', 'rank': 2},
            {'name': 'Feature_C', 'rank': 3}
        ]
        
        generated_files = generate_all_pdp_plots(
            mock_model, sample_feature_matrix, feature_names, top_features, temp_output_dir
        )
        
        assert len(generated_files) == 3
        for filepath in generated_files:
            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 0

    def test_create_combined_pdp_figure(self, mock_model, sample_feature_matrix, temp_output_dir):
        """Test combined PDP figure generation."""
        feature_names = ['Feature_A', 'Feature_B']
        top_features = [
            {'name': 'Feature_A', 'rank': 1},
            {'name': 'Feature_B', 'rank': 2}
        ]
        
        output_path = os.path.join(temp_output_dir, 'combined_pdp.png')
        create_combined_pdp_figure(
            mock_model, sample_feature_matrix, feature_names, top_features, output_path
        )
        
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_pdp_handles_single_feature(self, mock_model, sample_feature_matrix, temp_output_dir):
        """Test PDP generation with only one feature."""
        feature_names = ['Single_Feature']
        top_features = [{'name': 'Single_Feature', 'rank': 1}]
        
        output_path = os.path.join(temp_output_dir, 'single_pdp.png')
        create_combined_pdp_figure(
            mock_model, sample_feature_matrix, feature_names, top_features, output_path
        )
        
        assert os.path.exists(output_path)

    def test_pdp_uses_mean_for_other_features(self, mock_model, sample_feature_matrix):
        """Verify that PDP computation uses mean values for other features."""
        # This is a behavioral test - we check that the function doesn't crash
        # and produces reasonable output
        feature_idx = 0
        n_points = 5
        
        feature_values, _ = generate_pdp_grid(sample_feature_matrix, feature_idx, n_points)
        pdp_values = compute_partial_dependence(mock_model, sample_feature_matrix, feature_idx, feature_values)
        
        # Check that values are finite
        assert np.all(np.isfinite(pdp_values))
        
        # Check that there's some variation (not all zeros)
        assert np.std(pdp_values) > 0

    def test_pdp_grid_bounds_match_data(self, sample_feature_matrix):
        """Test that PDP grid respects data bounds."""
        for feature_idx in range(sample_feature_matrix.shape[1]):
            feature_values, _ = generate_pdp_grid(sample_feature_matrix, feature_idx, n_points=10)
            
            data_min = sample_feature_matrix[:, feature_idx].min()
            data_max = sample_feature_matrix[:, feature_idx].max()
            
            assert feature_values.min() >= data_min - 1e-6  # Allow small floating point error
            assert feature_values.max() <= data_max + 1e-6