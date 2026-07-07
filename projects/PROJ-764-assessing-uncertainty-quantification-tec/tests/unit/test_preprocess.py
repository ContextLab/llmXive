"""
Unit tests for code/data/preprocess.py focusing on PCA application and missing data exclusion.
These tests verify the logic of apply_pca and exclude_missing_data functions.
"""
import os
import sys
import tempfile
import json
import pytest
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split

# Add the project root to the path to import code/data modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.preprocess import (
    load_config,
    load_data,
    exclude_missing_data,
    stratified_split,
    apply_pca
)


class TestExcludeMissingData:
    """Tests for the exclude_missing_data function."""

    def test_exclude_missing_data_removes_rows(self):
        """Test that rows with missing values are correctly excluded."""
        # Create a test dataframe with some missing values
        data = {
            'feature_1': [1.0, 2.0, np.nan, 4.0, 5.0],
            'feature_2': [10.0, np.nan, 30.0, 40.0, 50.0],
            'feature_3': [100.0, 200.0, 300.0, 400.0, 500.0],
            'target': [1.0, 2.0, 3.0, 4.0, 5.0]
        }
        df = pd.DataFrame(data)

        # Call the function
        result_df, excluded_count, missing_cols = exclude_missing_data(df)

        # Verify the count of excluded rows (2 rows have NaN)
        assert excluded_count == 2
        assert len(result_df) == 3

        # Verify the missing columns are reported
        assert set(missing_cols) == {'feature_1', 'feature_2'}

        # Verify the remaining dataframe has no NaN values
        assert result_df.isnull().sum().sum() == 0

    def test_exclude_missing_data_no_missing(self):
        """Test behavior when there are no missing values."""
        data = {
            'feature_1': [1.0, 2.0, 3.0],
            'feature_2': [10.0, 20.0, 30.0],
            'target': [1.0, 2.0, 3.0]
        }
        df = pd.DataFrame(data)

        result_df, excluded_count, missing_cols = exclude_missing_data(df)

        assert excluded_count == 0
        assert len(result_df) == 3
        assert len(missing_cols) == 0
        assert result_df.equals(df)

    def test_exclude_missing_data_all_missing(self):
        """Test behavior when all rows have missing values."""
        data = {
            'feature_1': [np.nan, np.nan],
            'feature_2': [np.nan, np.nan],
            'target': [1.0, 2.0]
        }
        df = pd.DataFrame(data)

        result_df, excluded_count, missing_cols = exclude_missing_data(df)

        assert excluded_count == 2
        assert len(result_df) == 0


class TestApplyPCA:
    """Tests for the apply_pca function."""

    def test_apply_pca_reduces_dimensions(self):
        """Test that PCA reduces features to the specified number of components."""
        # Create a dataframe with more features than components
        np.random.seed(42)
        n_samples = 100
        n_features = 50
        n_components = 20

        data = {
            f'feature_{i}': np.random.rand(n_samples) for i in range(n_features)
        }
        data['target'] = np.random.rand(n_samples)
        df = pd.DataFrame(data)

        # Separate features and target
        features = df.drop(columns=['target'])
        target = df['target']

        # Apply PCA
        reduced_features, explained_variance = apply_pca(
            features,
            n_components=n_components,
            random_state=42
        )

        # Verify the number of components
        assert reduced_features.shape[1] == n_components
        assert len(explained_variance) == n_components

        # Verify the shape of the output
        assert reduced_features.shape[0] == n_samples

    def test_apply_pca_deterministic(self):
        """Test that PCA produces deterministic results with fixed random_state."""
        np.random.seed(42)
        n_samples = 50
        n_features = 20
        n_components = 5

        data = {
            f'feature_{i}': np.random.rand(n_samples) for i in range(n_features)
        }
        data['target'] = np.random.rand(n_samples)
        df = pd.DataFrame(data)

        features = df.drop(columns=['target'])

        # Run PCA twice
        result1, _ = apply_pca(features, n_components=n_components, random_state=42)
        result2, _ = apply_pca(features, n_components=n_components, random_state=42)

        # Results should be identical
        pd.testing.assert_frame_equal(result1, result2)

    def test_apply_pca_with_less_features_than_components(self):
        """Test PCA when requested components > available features."""
        np.random.seed(42)
        n_samples = 50
        n_features = 5
        n_components = 10  # More than available features

        data = {
            f'feature_{i}': np.random.rand(n_samples) for i in range(n_features)
        }
        data['target'] = np.random.rand(n_samples)
        df = pd.DataFrame(data)

        features = df.drop(columns=['target'])

        # Should handle gracefully or raise an error depending on implementation
        # For this test, we expect it to handle it by using max possible components
        try:
            reduced_features, _ = apply_pca(
                features,
                n_components=n_components,
                random_state=42
            )
            # If it doesn't raise, it should have used max possible components
            assert reduced_features.shape[1] <= n_features
        except ValueError:
            # Or it might raise an error if implementation doesn't handle this case
            pass


class TestIntegration:
    """Integration tests combining multiple preprocess functions."""

    def test_full_preprocess_pipeline(self):
        """Test the full pipeline: load -> exclude missing -> PCA."""
        # Create a temporary directory for test data
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a synthetic dataset with missing values
            np.random.seed(42)
            n_samples = 200
            n_features = 30

            data = {
                f'feature_{i}': np.random.rand(n_samples) for i in range(n_features)
            }
            # Introduce missing values
            data['feature_5'][np.random.choice(n_samples, 20, replace=False)] = np.nan
            data['feature_15'][np.random.choice(n_samples, 15, replace=False)] = np.nan
            data['target'] = np.random.rand(n_samples)

            df = pd.DataFrame(data)

            # Save to CSV
            csv_path = os.path.join(tmpdir, 'test_data.csv')
            df.to_csv(csv_path, index=False)

            # Load the data
            loaded_df = load_data(csv_path)

            # Exclude missing data
            clean_df, excluded_count, missing_cols = exclude_missing_data(loaded_df)

            # Verify exclusion
            assert excluded_count > 0
            assert 'feature_5' in missing_cols
            assert 'feature_15' in missing_cols

            # Apply PCA
            features = clean_df.drop(columns=['target'])
            target = clean_df['target']

            reduced_features, explained_var = apply_pca(
                features,
                n_components=20,
                random_state=42
            )

            # Verify PCA output
            assert reduced_features.shape[1] == 20
            assert len(explained_var) == 20
            assert reduced_features.shape[0] == len(clean_df)