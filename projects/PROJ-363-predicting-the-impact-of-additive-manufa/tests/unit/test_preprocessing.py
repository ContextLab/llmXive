import os
import sys
import pytest
import pandas as pd
import numpy as np
import tempfile
import json

# Import the functions from the actual implementation
# We need to add the code directory to the path to import preprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from preprocess import (
    normalize_column_synonyms,
    impute_missing_values,
    filter_invalid_rows,
    calculate_energy_density,
    normalize_features,
    create_feature_subsets,
    check_degenerate_dataset,
    write_degenerate_flag,
    update_state_degenerate,
    validate_schema
)
from utils import load_state, update_state

class TestNormalization:
    """Test suite for normalization scaling to [0, 1] range."""

    def test_normalize_features_basic(self):
        """Test that normalization scales features to [0, 1] range."""
        # Create a simple DataFrame with known min/max
        data = {
            'laser_power': [100.0, 200.0, 300.0],
            'scan_speed': [500.0, 1000.0, 1500.0],
            'hatch_spacing': [0.05, 0.1, 0.15],
            'layer_thickness': [0.02, 0.04, 0.06]
        }
        df = pd.DataFrame(data)

        # Normalize the features
        normalized_df = normalize_features(df)

        # Check that all normalized values are in [0, 1] range
        for col in ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']:
            assert normalized_df[col].min() >= 0.0 - 1e-9, f"Min value for {col} is below 0"
            assert normalized_df[col].max() <= 1.0 + 1e-9, f"Max value for {col} is above 1"

        # Check that the original min maps to 0 and max maps to 1
        assert np.isclose(normalized_df['laser_power'].min(), 0.0)
        assert np.isclose(normalized_df['laser_power'].max(), 1.0)
        assert np.isclose(normalized_df['scan_speed'].min(), 0.0)
        assert np.isclose(normalized_df['scan_speed'].max(), 1.0)

    def test_normalize_features_single_value(self):
        """Test normalization with a single unique value (should result in all 0s or handled gracefully)."""
        data = {
            'laser_power': [100.0, 100.0, 100.0],
            'scan_speed': [500.0, 500.0, 500.0],
            'hatch_spacing': [0.05, 0.05, 0.05],
            'layer_thickness': [0.02, 0.02, 0.02]
        }
        df = pd.DataFrame(data)

        # Normalize - this should handle the zero variance case
        # The implementation should either set to 0.0 or raise a specific error
        # For this test, we expect it to run without crashing and produce valid output
        normalized_df = normalize_features(df)

        # With zero variance, min=max, so (x-min)/(max-min) would be 0/0
        # The implementation should handle this by setting all values to 0.0 or 0.5
        # Let's check that the output is still in [0, 1]
        for col in ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']:
            assert normalized_df[col].min() >= 0.0 - 1e-9
            assert normalized_df[col].max() <= 1.0 + 1e-9

    def test_normalize_features_preserves_shape(self):
        """Test that normalization preserves the DataFrame shape."""
        data = {
            'laser_power': [100.0, 200.0, 300.0, 400.0],
            'scan_speed': [500.0, 1000.0, 1500.0, 2000.0],
            'hatch_spacing': [0.05, 0.1, 0.15, 0.2],
            'layer_thickness': [0.02, 0.04, 0.06, 0.08]
        }
        df = pd.DataFrame(data)

        normalized_df = normalize_features(df)

        assert normalized_df.shape == df.shape
        assert list(normalized_df.columns) == list(df.columns)

    def test_normalize_features_with_nan(self):
        """Test normalization handles NaN values appropriately."""
        data = {
            'laser_power': [100.0, np.nan, 300.0],
            'scan_speed': [500.0, 1000.0, np.nan],
            'hatch_spacing': [0.05, 0.1, 0.15],
            'layer_thickness': [0.02, 0.04, 0.06]
        }
        df = pd.DataFrame(data)

        # Normalize - NaN values should remain NaN
        normalized_df = normalize_features(df)

        # Check that NaN positions are preserved
        assert pd.isna(normalized_df.loc[1, 'laser_power'])
        assert pd.isna(normalized_df.loc[2, 'scan_speed'])

        # Check that non-NaN values are in [0, 1]
        assert normalized_df.loc[0, 'laser_power'] >= 0.0
        assert normalized_df.loc[0, 'laser_power'] <= 1.0
        assert normalized_df.loc[2, 'laser_power'] >= 0.0
        assert normalized_df.loc[2, 'laser_power'] <= 1.0

    def test_normalize_features_edge_case_zero_range(self):
        """Test normalization when max equals min for a column."""
        data = {
            'laser_power': [100.0, 100.0, 100.0],  # Zero range
            'scan_speed': [500.0, 1000.0, 1500.0],  # Normal range
            'hatch_spacing': [0.05, 0.1, 0.15],
            'layer_thickness': [0.02, 0.04, 0.06]
        }
        df = pd.DataFrame(data)

        # This should not crash and should produce valid output
        normalized_df = normalize_features(df)

        # Check that laser_power (zero range) is handled
        # Typically set to 0.0 or 0.5 to avoid division by zero
        assert normalized_df['laser_power'].min() >= 0.0
        assert normalized_df['laser_power'].max() <= 1.0

        # Check that other columns are properly normalized
        assert np.isclose(normalized_df['scan_speed'].min(), 0.0)
        assert np.isclose(normalized_df['scan_speed'].max(), 1.0)

    def test_normalize_features_realistic_data(self):
        """Test normalization with more realistic data ranges."""
        # Simulate realistic LPBF parameters
        np.random.seed(42)
        data = {
            'laser_power': np.random.uniform(100, 400, 100),
            'scan_speed': np.random.uniform(400, 1200, 100),
            'hatch_spacing': np.random.uniform(0.03, 0.15, 100),
            'layer_thickness': np.random.uniform(0.02, 0.06, 100)
        }
        df = pd.DataFrame(data)

        normalized_df = normalize_features(df)

        # Verify all values are in [0, 1]
        for col in df.columns:
            assert normalized_df[col].min() >= 0.0 - 1e-9
            assert normalized_df[col].max() <= 1.0 + 1e-9

            # Verify min maps to 0 and max maps to 1 (with tolerance for floating point)
            assert np.isclose(normalized_df[col].min(), 0.0, atol=1e-9)
            assert np.isclose(normalized_df[col].max(), 1.0, atol=1e-9)

    def test_normalize_features_column_order(self):
        """Test that normalization preserves column order."""
        data = {
            'laser_power': [100.0, 200.0],
            'scan_speed': [500.0, 1000.0],
            'hatch_spacing': [0.05, 0.1],
            'layer_thickness': [0.02, 0.04]
        }
        df = pd.DataFrame(data)

        normalized_df = normalize_features(df)

        # Check column order is preserved
        assert list(normalized_df.columns) == list(df.columns)

    def test_normalize_features_with_outliers(self):
        """Test normalization handles outliers correctly."""
        data = {
            'laser_power': [100.0, 200.0, 300.0, 1000.0],  # Outlier at 1000
            'scan_speed': [500.0, 1000.0, 1500.0, 2000.0],
            'hatch_spacing': [0.05, 0.1, 0.15, 0.2],
            'layer_thickness': [0.02, 0.04, 0.06, 0.08]
        }
        df = pd.DataFrame(data)

        normalized_df = normalize_features(df)

        # The outlier should still be in [0, 1], just closer to 1
        assert normalized_df.loc[3, 'laser_power'] == 1.0  # Max value
        assert normalized_df.loc[0, 'laser_power'] == 0.0  # Min value

        # All values should be in [0, 1]
        for col in df.columns:
            assert normalized_df[col].min() >= 0.0 - 1e-9
            assert normalized_df[col].max() <= 1.0 + 1e-9

class TestPreprocessingIntegration:
    """Integration tests for the full preprocessing pipeline."""

    def test_full_pipeline_normalization(self):
        """Test that the full preprocessing pipeline includes normalization."""
        # Create a temporary directory for test files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test CSV with raw data
            raw_data = {
                'laser_power': [100.0, 200.0, 300.0, 400.0],
                'scan_speed': [500.0, 1000.0, 1500.0, 2000.0],
                'hatch_spacing': [0.05, 0.1, 0.15, 0.2],
                'layer_thickness': [0.02, 0.04, 0.06, 0.08],
                'porosity': [0.1, 0.2, 0.3, 0.4]
            }
            raw_df = pd.DataFrame(raw_data)
            raw_path = os.path.join(tmpdir, 'test_raw.csv')
            raw_df.to_csv(raw_path, index=False)

            # Create schema file
            schema = {
                'columns': [
                    {'name': 'laser_power', 'type': 'float'},
                    {'name': 'scan_speed', 'type': 'float'},
                    {'name': 'hatch_spacing', 'type': 'float'},
                    {'name': 'layer_thickness', 'type': 'float'},
                    {'name': 'porosity', 'type': 'float'}
                ]
            }
            schema_path = os.path.join(tmpdir, 'schema.yaml')
            with open(schema_path, 'w') as f:
                import yaml
                yaml.dump(schema, f)

            # Run the preprocessing steps
            df = pd.read_csv(raw_path)
            df = normalize_column_synonyms(df)
            df = impute_missing_values(df)
            df = filter_invalid_rows(df)
            df = calculate_energy_density(df)
            df = normalize_features(df)

            # Verify normalization was applied
            for col in ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']:
                assert df[col].min() >= 0.0 - 1e-9
                assert df[col].max() <= 1.0 + 1e-9

    def test_feature_subsets_created_correctly(self):
        """Test that feature subsets are created with normalized data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data
            data = {
                'laser_power': [100.0, 200.0, 300.0],
                'scan_speed': [500.0, 1000.0, 1500.0],
                'hatch_spacing': [0.05, 0.1, 0.15],
                'layer_thickness': [0.02, 0.04, 0.06],
                'porosity': [0.1, 0.2, 0.3]
            }
            df = pd.DataFrame(data)

            # Create feature subsets
            X_raw, X_derived = create_feature_subsets(df)

            # Check that X_raw contains normalized raw parameters
            assert 'laser_power' in X_raw.columns
            assert 'scan_speed' in X_raw.columns
            assert 'hatch_spacing' in X_raw.columns
            assert 'layer_thickness' in X_raw.columns

            # Check that X_raw values are in [0, 1]
            for col in X_raw.columns:
                assert X_raw[col].min() >= 0.0 - 1e-9
                assert X_raw[col].max() <= 1.0 + 1e-9

            # Check that X_derived contains energy_density (if calculated)
            if 'energy_density' in df.columns:
                assert 'energy_density' in X_derived.columns