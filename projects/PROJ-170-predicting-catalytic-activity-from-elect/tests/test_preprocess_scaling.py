import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import pytest
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from preprocess import (
    get_numeric_feature_columns,
    scale_features,
    save_scaler
)

class TestScalingLogic:
    """Unit tests for the scaling logic in T019."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame with mixed types."""
        data = {
            'composition': ['Fe2O3', 'CuO', 'ZnO', 'TiO2'],
            'surface_facet': ['001', '100', '110', '001'],
            'entry_id': ['a', 'b', 'c', 'd'],
            'experimental_tof': [1.0, 2.0, 3.0, 4.0],  # Target - should NOT be scaled
            'd_band_center': [-2.5, -1.8, -3.2, -2.1],
            'adsorption_energy': [-1.5, -2.2, -1.8, -2.0],
            'stoich_Fe': [0.66, 0.0, 0.0, 0.0],
            'stoich_O': [0.33, 0.5, 0.5, 0.66],
            'stoich_Cu': [0.0, 0.5, 0.0, 0.0],
            'stoich_Zn': [0.0, 0.0, 0.5, 0.0],
            'stoich_Ti': [0.0, 0.0, 0.0, 0.33]
        }
        return pd.DataFrame(data)

    def test_numeric_feature_detection_excludes_target(self, sample_dataframe):
        """Verify that experimental_tof is excluded from scaling features."""
        cols = get_numeric_feature_columns(sample_dataframe)
        
        assert 'experimental_tof' not in cols, "Target variable should not be in feature list"
        assert 'd_band_center' in cols, "Numeric feature should be included"
        assert 'adsorption_energy' in cols, "Numeric feature should be included"
        assert 'stoich_Fe' in cols, "Stoichiometry feature should be included"
        
        # String columns should be excluded
        assert 'composition' not in cols
        assert 'surface_facet' not in cols
        assert 'entry_id' not in cols

    def test_scaling_produces_zero_mean_unit_variance(self, sample_dataframe):
        """Verify that scaling results in mean ~0 and std ~1 for features."""
        feature_cols = get_numeric_feature_columns(sample_dataframe)
        
        df_scaled, scaler = scale_features(sample_dataframe, feature_cols)
        
        # Check that scaled features have mean close to 0
        scaled_means = df_scaled[feature_cols].mean()
        assert np.allclose(scaled_means, 0, atol=1e-6), f"Scaled means should be ~0, got {scaled_means}"
        
        # Check that scaled features have std close to 1
        scaled_stds = df_scaled[feature_cols].std(ddof=0)  # StandardScaler uses population std
        assert np.allclose(scaled_stds, 1, atol=1e-6), f"Scaled stds should be ~1, got {scaled_stds}"

    def test_target_variable_unchanged(self, sample_dataframe):
        """Verify that the target variable is not scaled."""
        feature_cols = get_numeric_feature_columns(sample_dataframe)
        
        df_scaled, _ = scale_features(sample_dataframe, feature_cols)
        
        # Target should remain exactly as original
        original_tof = sample_dataframe['experimental_tof'].values
        scaled_tof = df_scaled['experimental_tof'].values
        
        assert np.array_equal(original_tof, scaled_tof), "Target variable should not be modified"

    def test_scaler_metadata_saving(self, sample_dataframe, tmp_path):
        """Test that scaler metadata can be saved and loaded correctly."""
        feature_cols = get_numeric_feature_columns(sample_dataframe)
        _, scaler = scale_features(sample_dataframe, feature_cols)
        
        output_path = tmp_path / 'scaler_test.json'
        save_scaler(scaler, feature_cols, output_path)
        
        assert output_path.exists(), "Scaler metadata file should be created"
        
        with open(output_path, 'r') as f:
            metadata = json.load(f)
        
        assert 'mean' in metadata
        assert 'scale' in metadata
        assert 'var' in metadata
        assert 'feature_names' in metadata
        assert metadata['feature_names'] == feature_cols

    def test_no_nan_in_scaled_output(self, sample_dataframe):
        """Verify that scaling does not introduce NaN values."""
        feature_cols = get_numeric_feature_columns(sample_dataframe)
        
        df_scaled, _ = scale_features(sample_dataframe, feature_cols)
        
        nan_counts = df_scaled.isna().sum()
        assert nan_counts.sum() == 0, f"Scaling introduced NaN values: {nan_counts}"

class TestEdgeCases:
    """Tests for edge cases in scaling."""

    def test_empty_feature_list(self):
        """Handle case where no numeric features exist."""
        df = pd.DataFrame({
            'composition': ['A', 'B'],
            'experimental_tof': [1.0, 2.0]
        })
        
        feature_cols = get_numeric_feature_columns(df)
        assert len(feature_cols) == 0, "No numeric features should be found"
        
        df_scaled, scaler = scale_features(df, feature_cols)
        assert df_scaled.equals(df), "DataFrame should remain unchanged when no features to scale"

    def test_single_row(self):
        """Handle single row edge case."""
        df = pd.DataFrame({
            'composition': ['Fe2O3'],
            'd_band_center': [-2.5],
            'experimental_tof': [1.0]
        })
        
        feature_cols = get_numeric_feature_columns(df)
        df_scaled, _ = scale_features(df, feature_cols)
        
        # Single row scaling: mean=that value, std=0 -> results in 0
        # This is expected behavior for StandardScaler
        assert df_scaled['d_band_center'].iloc[0] == 0.0, "Single row should scale to 0"