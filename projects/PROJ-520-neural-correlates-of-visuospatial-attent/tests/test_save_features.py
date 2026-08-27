"""
Tests for T023: Save feature matrix functionality.
"""
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from save_features import save_feature_matrix


class TestSaveFeatureMatrix:
    """Test cases for save_feature_matrix function."""

    def test_save_feature_matrix_basic(self, tmp_path):
        """Test basic saving of feature matrix."""
        # Create test data
        matrix = np.array([
            [0.5, 0.8, 0.3],
            [0.6, 0.7, 0.4],
            [0.7, 0.6, 0.5]
        ])
        labels = ['alpha_p3', 'alpha_pz', 'beta_f3']
        epoch_ids = ['epoch_001', 'epoch_002', 'epoch_003']

        features = {
            'matrix': matrix,
            'labels': labels,
            'epoch_ids': epoch_ids
        }

        output_path = tmp_path / 'features_matrix.csv'

        # Save
        save_feature_matrix(features, output_path)

        # Verify file exists
        assert output_path.exists()

        # Verify contents
        df = pd.read_csv(output_path)

        # Check dimensions
        assert df.shape == (3, 4)  # 3 epochs, 1 ID + 3 features

        # Check column names
        expected_columns = ['epoch_id'] + labels
        assert list(df.columns) == expected_columns

        # Check epoch IDs
        assert list(df['epoch_id']) == epoch_ids

        # Check feature values
        np.testing.assert_array_almost_equal(df[labels].values, matrix)

    def test_save_feature_matrix_single_epoch(self, tmp_path):
        """Test saving with a single epoch."""
        matrix = np.array([[0.5, 0.8]])
        labels = ['alpha_p3', 'alpha_pz']
        epoch_ids = ['epoch_001']

        features = {
            'matrix': matrix,
            'labels': labels,
            'epoch_ids': epoch_ids
        }

        output_path = tmp_path / 'features_matrix.csv'
        save_feature_matrix(features, output_path)

        df = pd.read_csv(output_path)
        assert df.shape == (1, 3)
        assert df['epoch_id'].iloc[0] == 'epoch_001'

    def test_save_feature_matrix_creates_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        matrix = np.array([[0.5, 0.8]])
        labels = ['alpha_p3']
        epoch_ids = ['epoch_001']

        features = {
            'matrix': matrix,
            'labels': labels,
            'epoch_ids': epoch_ids
        }

        # Create a nested path that doesn't exist
        output_path = tmp_path / 'deep' / 'nested' / 'path' / 'features_matrix.csv'
        assert not output_path.parent.exists()

        save_feature_matrix(features, output_path)

        assert output_path.exists()

    def test_save_feature_matrix_mismatched_rows(self, tmp_path):
        """Test that mismatched rows and epoch IDs raises error."""
        matrix = np.array([[0.5, 0.8], [0.6, 0.7]])
        labels = ['alpha_p3', 'alpha_pz']
        epoch_ids = ['epoch_001']  # Only 1 ID for 2 rows

        features = {
            'matrix': matrix,
            'labels': labels,
            'epoch_ids': epoch_ids
        }

        output_path = tmp_path / 'features_matrix.csv'

        with pytest.raises(ValueError, match="Number of rows"):
            save_feature_matrix(features, output_path)

    def test_save_feature_matrix_mismatched_cols(self, tmp_path):
        """Test that mismatched columns and labels raises error."""
        matrix = np.array([[0.5, 0.8]])
        labels = ['alpha_p3']  # Only 1 label for 2 columns
        epoch_ids = ['epoch_001']

        features = {
            'matrix': matrix,
            'labels': labels,
            'epoch_ids': epoch_ids
        }

        output_path = tmp_path / 'features_matrix.csv'

        with pytest.raises(ValueError, match="Number of columns"):
            save_feature_matrix(features, output_path)

    def test_save_feature_matrix_large_matrix(self, tmp_path):
        """Test saving a larger feature matrix."""
        n_epochs = 100
        n_features = 10

        matrix = np.random.rand(n_epochs, n_features)
        labels = [f'feature_{i}' for i in range(n_features)]
        epoch_ids = [f'epoch_{i:03d}' for i in range(n_epochs)]

        features = {
            'matrix': matrix,
            'labels': labels,
            'epoch_ids': epoch_ids
        }

        output_path = tmp_path / 'features_matrix.csv'
        save_feature_matrix(features, output_path)

        df = pd.read_csv(output_path)
        assert df.shape == (n_epochs, n_features + 1)

        # Verify all epoch IDs are present
        assert set(df['epoch_id']) == set(epoch_ids)

    def test_save_feature_matrix_with_nan_values(self, tmp_path):
        """Test saving matrix with NaN values."""
        matrix = np.array([
            [0.5, np.nan, 0.3],
            [0.6, 0.7, 0.4],
            [np.nan, 0.6, 0.5]
        ])
        labels = ['alpha_p3', 'alpha_pz', 'beta_f3']
        epoch_ids = ['epoch_001', 'epoch_002', 'epoch_003']

        features = {
            'matrix': matrix,
            'labels': labels,
            'epoch_ids': epoch_ids
        }

        output_path = tmp_path / 'features_matrix.csv'
        save_feature_matrix(features, output_path)

        df = pd.read_csv(output_path)
        assert df.shape == (3, 4)
        # NaN values should be preserved as empty in CSV
        assert df['alpha_p3'].isna().sum() == 1
        assert df['alpha_pz'].isna().sum() == 1