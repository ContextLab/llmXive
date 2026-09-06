import pytest
import pandas as pd
import numpy as np
import os
import sys
import tempfile
from pathlib import Path

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from preprocess import create_feature_subsets, normalize_columns, handle_ev_fallback

class TestFeatureSubsets:
    """Tests for T016b: Creating distinct feature subsets X_raw and X_derived."""

    def setup_method(self):
        """Create a mock dataframe for testing."""
        self.df = pd.DataFrame({
            'laser_power': [100.0, 200.0, 300.0],
            'scan_speed': [500.0, 600.0, 700.0],
            'hatch_spacing': [0.1, 0.15, 0.2],
            'layer_thickness': [0.03, 0.04, 0.05],
            'energy_density': [6.67, 5.56, 4.29],
            'porosity': [0.05, 0.08, 0.12]
        })

    def test_create_feature_subsets_exists(self):
        """Verify that create_feature_subsets returns two DataFrames."""
        X_raw, X_derived = create_feature_subsets(self.df)
        
        assert isinstance(X_raw, pd.DataFrame)
        assert isinstance(X_derived, pd.DataFrame)

    def test_X_raw_columns(self):
        """Verify X_raw contains only raw parameters."""
        X_raw, _ = create_feature_subsets(self.df)
        
        expected_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
        assert list(X_raw.columns) == expected_cols
        assert len(X_raw.columns) == 4

    def test_X_derived_columns(self):
        """Verify X_derived contains only the derived parameter."""
        _, X_derived = create_feature_subsets(self.df)
        
        expected_cols = ['energy_density']
        assert list(X_derived.columns) == expected_cols
        assert len(X_derived.columns) == 1

    def test_X_raw_values(self):
        """Verify X_raw values match the original data."""
        X_raw, _ = create_feature_subsets(self.df)
        
        assert np.allclose(X_raw['laser_power'].values, self.df['laser_power'].values)
        assert np.allclose(X_raw['scan_speed'].values, self.df['scan_speed'].values)
        assert np.allclose(X_raw['hatch_spacing'].values, self.df['hatch_spacing'].values)
        assert np.allclose(X_raw['layer_thickness'].values, self.df['layer_thickness'].values)

    def test_X_derived_values(self):
        """Verify X_derived values match the original data."""
        _, X_derived = create_feature_subsets(self.df)
        
        assert np.allclose(X_derived['energy_density'].values, self.df['energy_density'].values)

    def test_missing_raw_columns_raises_error(self):
        """Verify that missing raw columns raise an error."""
        df_missing = self.df.drop(columns=['laser_power'])
        
        with pytest.raises(ValueError) as excinfo:
            create_feature_subsets(df_missing)
        
        assert "Missing raw feature columns" in str(excinfo.value)

    def test_missing_derived_column_raises_error(self):
        """Verify that missing derived column raises an error."""
        df_missing = self.df.drop(columns=['energy_density'])
        
        with pytest.raises(ValueError) as excinfo:
            create_feature_subsets(df_missing)
        
        assert "Missing derived feature column" in str(excinfo.value)

    def test_fr_010_enforcement(self):
        """Verify that X_raw and X_derived are mutually exclusive (no overlap)."""
        X_raw, X_derived = create_feature_subsets(self.df)
        
        raw_cols = set(X_raw.columns)
        derived_cols = set(X_derived.columns)
        
        overlap = raw_cols.intersection(derived_cols)
        assert len(overlap) == 0, f"FR-010 violation: Overlapping columns {overlap}"